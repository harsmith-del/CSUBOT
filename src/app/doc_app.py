import os
import sys
from pathlib import Path
import json

from loguru import logger
from fastapi import FastAPI, Response, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
from elasticsearch import Elasticsearch

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from pipelines import pipeline_factory
from indexer.build_indices import build_index as _build_index
from util import connect_to_docstore
from util.vars import CONTEXT, FRAGMENT_TO_CONTEXT, ES_INDEX

#FastAPI Pydantic datamodels
class SearchData(BaseModel):
    """ Data model for single query search
        query: search query
        n_retrieve: number of document fragments to retrieve
        n_rank: number of documents to retain after ranking """
    query: str
    n_retrieve: int = 10
    n_rank: int = 5

class PipelineParams(BaseModel):
    """ Data model for search pipeline
        retriever: retriever type, approach to finding relevant document sections
            must match retriever used to build search index
        enricher: document enricher - additions to retrieved document sections
        summarizer: document summarizer to use: local or openai
        document: selected document to search
    """
    retriever: str = 'Embedding'
    enricher: str = 'next_document'
    summarizer: str = 'local'
    document: str = 'doc_embedding'

class IndexParams(BaseModel):
    """ Data model for search index creation
        doc_name: name of document, used for es_index name
        data_path: path in container to documents for indexing
        ds_path: document store path - where file-based document stores will be saved
        retriever: retriever type, approach to finding relevant document sections
        docstore_type: type of document store (~document database)
    """
    doc_name: str = 'document', 
    data_path: str = '/tmp/data', 
    ds_path: str = '/tmp/data', 
    retriever: str ='Embedding', 
    docstore_type: str = 'elasticsearch'

#FastAPI app creation
def create_app() -> FastAPI:
    app = FastAPI()
    app.pipelines = {}

    #setup logger
    logger.remove()
    logger.add("/tmp/logs/app_loguru.log")
    app.logger = logger
    return app

app = create_app()

#FastAPI routes
@app.get('/')
async def root() -> Response:
    """health check root route"""
    return 'this is the doc_app container'

@app.get('/documents')
async def documents() -> Response:
    """list of document stores available in document stores"""
    docstore_type = os.environ['DOCUMENT_STORE']

    app.logger.info(f'getting available documents')
    if docstore_type == 'elasticsearch':
        try:
            container_prefix = os.environ['CONTAINER_PREFIX']
        except KeyError:
            container_prefix = None
        es_host = f'{container_prefix}_es_haystack'

        es_client = Elasticsearch(
                        hosts=es_host,
                        scheme="http",
                    )
        res = es_client.indices.get_alias(index="*")
    else:
        raise NotImplementedError

    return res

@app.post('/search/{pipeline}')
async def search(pipeline: str, data: SearchData) -> Response:
    """search a document using the selected pipeline type:
    
    params:
        pipeline: type of search pipeline. currently summarization or qa
        data: SearchData parmaterizing the search
    """
    params={
        "Retriever": {"top_k": data.n_retrieve},
        "Ranker": {"top_k": data.n_rank}
    }
    app.logger.info(f'searching with query: {data.query} and pipeline: {pipeline}')

    try:
        app.pipelines[pipeline]
    except KeyError:
        default_retriever = 'Embedding'
        default_enricher = 'next_document'
        default_summarizer = 'local'

        f = open(CONTEXT.format(document=ES_INDEX))
        context_list = json.load(f)
        f = open(FRAGMENT_TO_CONTEXT.format(document=ES_INDEX))
        sentence_context_dict = json.load(f)
        sentence_context_dict = {int(k):v for k,v in sentence_context_dict.items()}
        document_store = connect_to_docstore(retriever=default_retriever,
                                             index=ES_INDEX)
        app.pipelines[pipeline] = pipeline_factory(pipeline_type = pipeline,
                                            document_store = document_store, 
                                            summarizer = default_summarizer, 
                                            retriever=default_retriever,
                                            enricher=default_enricher,
                                            sentence_context_connector=sentence_context_dict,
                                            context_store=context_list,)

    pipeline_type, result = app.pipelines[pipeline].run(data.query, params=params)
    response = app.pipelines[pipeline].prepare_response(result)
    return response
  
@app.post('/build_pipeline/{pipeline}')
async def build_pipeline(pipeline: str, params: PipelineParams) -> Response:
    """build a search pipeline
    
    params:
        pipeline: type of search pipeline. currently summarization or qa
        data: PipelineParams parmaterizing the search pipeline
    """
    app.logger.info(f'rebuidling the {pipeline} pipeline for document: {params.document}, summarizer {params.summarizer}')
    
    f = open(CONTEXT.format(document=params.document))
    context_list = json.load(f)
    f = open(FRAGMENT_TO_CONTEXT.format(document=params.document))
    sentence_context_dict = json.load(f)
    sentence_context_dict = {int(k):v for k,v in sentence_context_dict.items()}
    document_store = connect_to_docstore(retriever=params.retriever,
                                         index=params.document)
    app.pipelines[pipeline] = pipeline_factory(pipeline_type = pipeline,
                                        document_store = document_store, 
                                        summarizer=params.summarizer,
                                        retriever=params.retriever,
                                        enricher=params.enricher, 
                                        sentence_context_connector=sentence_context_dict,
                                        context_store=context_list,)
    return {'success': True}

@app.post('/build_index')
async def build_index(index_params: IndexParams) -> Response:
    """build a search index on a document or set of documents

    WARNING: this can be a time consuming step depending on document size
    and retriever type selected
    params:
        data: IndexParams parmaterizing the index to be built
    """
    app.logger.info(f'building index: {index_params.dict()}')
    try:
        _build_index(doc_name = index_params.doc_name, 
                    data_path = index_params.data_path, 
                    ds_path = index_params.ds_path, 
                    retriever = index_params.retriever, 
                    docstore_type = index_params.docstore_type)
        
        app.logger.info(f'successfully built index: {index_params.dict()}')
        return {'success': True}
    except Exception as e:
        return {'success': False,
                'error': str(e)}
    
@app.post("/upload")
async def create_upload_file(document: str = Form(...),
                             filename: str = Form(...),
                             file: UploadFile = File(...)):
    """upload files to build an index
    
    parms:
        document: name of document or set of documents - will create a folder
            named "document" where all files of this "document" will be saved
        filename: name of the file being upload
        file: actual binary file uploaded
    """
    app.logger.info(f'in upload file')
    folder = Path(f'/tmp/data/uploads/{document}')
    folder.mkdir(exist_ok=True, parents=True)
    filepath = folder / filename
    try:
        contents = file.file.read()
        with open(filepath, 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    app.logger.info(f"Successfully uploaded {filename} for {document}")
    return {"message": f"Successfully uploaded {filename} for {document}"}


def run():
    """run FASTapi app on uvicorn server"""
    uvicorn.run("doc_app:app", 
                host="0.0.0.0", 
                port=5000,
                reload=True,
                log_config = "./app/uvicorn_log.ini")

if __name__ == "__main__":
    run()
