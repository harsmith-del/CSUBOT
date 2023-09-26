import os
import sys
import logging
from pathlib import Path

import time
from loguru import logger

from haystack.document_stores import ElasticsearchDocumentStore, \
                FAISSDocumentStore, SQLDocumentStore
from haystack.nodes import EmbeddingRetriever

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import DOCExtractorDefault
from indexer import DOCIndexer
from util.vars import EMBEDDING_MODEL, EMBEDDING_MODEL_FORMAT

#build indices for desired retriever types

def build_index(doc_name: str = 'PyramidDocs', 
                data_path: str = r"C:\Users\harsmith\Documents\GitHub\CSUBOT\data",
                ds_path: str = '/tmp/data', 
                retriever: str ='Embedding', 
                docstore_type: str = 'elasticsearch') -> None:
    """build document store index for later searching
    
    parameters:
        doc_name: str, name for document or group of documents, used for elasticsearch index name
        data_path: str, path to directory where raw documents are held
        ds_path: str, document store path for file-based document stores
        retriever: str, retriever type, used for generating embeddings as needed
        docstore_type: str, type of document store: currently allows: sql, faiss, elasticsearch
    """
    data_path = r"C:\Users\harsmith\Documents\GitHub\CSUBOT\data"
    ds_path = Path(ds_path)
    try:
        container_prefix = os.environ['CONTAINER_PREFIX']
    except KeyError:
        container_prefix = None

    logger.debug(f' building index for retriever: {retriever}, docstore: {docstore_type}')
    if docstore_type == 'elasticsearch':
        es_host = f'{container_prefix}_es_haystack'
        document_store = ElasticsearchDocumentStore(
            host=es_host,
            username="",
            password="",
            index=doc_name,
            similarity="dot_product",
            embedding_dim=768
        )
    elif docstore_type == 'faiss':
        faiss_dir = ds_path / 'faiss_docstore'
        faiss_dir.mkdir(exist_ok=True, parents=True)
        document_store = FAISSDocumentStore(
                    sql_url = f'sqlite:///{str(faiss_dir)}/faiss_document_store_{doc_name}_{retriever}.db',
                    embedding_dim=768,
                    faiss_index_factory_str='Flat',
                )
    elif docstore_type == 'sql':
        sql_dir = ds_path / 'sql_docstore'
        sql_dir.mkdir(exist_ok=True, parents=True)
        document_store = SQLDocumentStore(f"sqlite:///{str(sql_dir)}/sql_index_{doc_name}_{retriever}.db")
    else:
        raise NotImplementedError(f'no known document store type: {docstore_type}')
  
    print("------------DATA PATH:",data_path)
    t_start = time.time()
    extracted_docs = DOCExtractorDefault(name=doc_name,
                                         dir=data_path)
    #print("Directory Name in Extractor:",extracted_docs.dir)
    indexer = DOCIndexer(document_store)
    if len(extracted_docs.get_fragments()) == 0:
        raise Exception("No data found, please add data or correct path.")
    indexer.add(extracted_docs.get_fragments())
    t_end = time.time()
    t_elapsed = t_end - t_start
    logger.debug(f'time to do indexing: {t_elapsed}')
    docstore_description = document_store.describe_documents()
    logger.debug(docstore_description)

    t_start = time.time()
    if docstore_type != 'sql' and retriever=='Embedding':
        _retriever = EmbeddingRetriever(
                document_store=document_store,
                embedding_model=EMBEDDING_MODEL,
                model_format=EMBEDDING_MODEL_FORMAT,
                use_gpu=True,
            )
        document_store.update_embeddings(_retriever)

    if docstore_type=='faiss':
        document_store.save(index_path=f'{str(faiss_dir)}/faiss_index_{doc_name}_{retriever}.bin')

    t_end = time.time()
    t_elapsed = t_end - t_start
    logger.debug(f'time to embed documents: {t_elapsed} s')

if __name__ == "__main__":
    docstore_type = os.environ['DOCUMENT_STORE']
    configs = [      #tuple of: doc_name, retriever, docstore type
                    ('doc_embedding','Embedding',  docstore_type),
                ]  
    for doc_name, retriever, _docstore_type in configs:
        build_index(doc_name = doc_name,
                    data_path = '/tmp/data/FAR_dita_html',
                    ds_path='/tmp/data', 
                    retriever=retriever,
                    docstore_type=_docstore_type)
