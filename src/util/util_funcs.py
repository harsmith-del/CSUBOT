import os
import re
from pathlib import Path
from typing import Tuple

from haystack.document_stores import ElasticsearchDocumentStore,\
             FAISSDocumentStore, SQLDocumentStore, BaseDocumentStore

retriever_to_index = { 
                        'Embedding' :'doc_embedding',
                        'DensePassage' : 'doc_densepassage',
                        'BM25' : 'doc_embedding',
                        'TfIdf' :'doc_embedding'
                    }

def connect_to_docstore(docstore_type: str = None,
                        ds_path: str ='/tmp/data', 
                        retriever: str ='Embedding',
                        index: str = None) -> BaseDocumentStore:
    """connect to document store
    
    parameters:
        docstore_type = str, Haystack DocumentStore type to connect to
        ds_path = str, path to document store data, when relevant
        retriever = str, type of retriever associated with document store, 
            used to determine index within document store

    return:
        document_store: Haystack DocumentStore
    """
    try:
        container_prefix = os.environ['CONTAINER_PREFIX']
    except KeyError:
        container_prefix = None
        
    if docstore_type is None:
        docstore_type = os.environ['DOCUMENT_STORE']

    if docstore_type == 'elasticsearch':
        es_host = f'{container_prefix}_es_haystack'
        if not index:
            index = retriever_to_index[retriever]
        document_store = ElasticsearchDocumentStore(
            host=es_host,
            username="",
            password="",
            index=index,
            similarity="dot_product",
            embedding_dim=768
        )
    elif docstore_type == 'faiss':
        document_store = FAISSDocumentStore.load(index_path = f'{ds_path}/faiss_docstore/faiss_index_doc_{retriever}.bin')
    elif docstore_type == 'sql':
        document_store = SQLDocumentStore(f"sqlite:///{ds_path}/sql_docstore/sql_index_doc_{retriever}.db")
    else: 
        raise NotImplementedError(f'no known document store type: {docstore_type}')
    
    return document_store
