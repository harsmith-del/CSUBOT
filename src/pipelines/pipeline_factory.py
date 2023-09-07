import os
import sys
from pathlib import Path
from typing import Dict

from haystack.document_stores import BaseDocumentStore

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from pipelines import SearchSummarizer, SearchQA


def pipeline_factory(pipeline_type: str, 
                    document_store: BaseDocumentStore, 
                    summarizer: str=None,
                    retriever: str=None,
                    enricher: str=None, 
                    sentence_context_connector: Dict=None,
                    context_store: Dict=None,):
    """ factory function to build search pipeline

    parameters:
        pipeline_type: type of pipeline to build: SearchSummarizer, SearchQA
        document_store: Haystack DocumentStore, document database to search
        summarizer: type of summarizer to use for pipeline
        retriever: str, specifies type of Haystack Retriever used to search document store
        enricher: str, specifies type of RetrievalEnricher to use
        sentence_context_connector: dict, dictionary to convert from the sentence uuid to context uuid/index
        context_store: dict, contains list of all full length context to match with each sentence
    returns:
        pipeline: SearchSummarizer, SearchQA
    """
    
    if pipeline_type == 'summarization':
        return SearchSummarizer(document_store = document_store, 
                    summarizer=summarizer,
                    retriever=retriever,
                    enricher=enricher,
                    sentence_context_connector=sentence_context_connector,
                    context_store=context_store,)
    
    elif pipeline_type == 'qa':
        return SearchQA(document_store = document_store, 
                    retriever=retriever,
                    enricher=enricher, )
    
    else: 
        raise NotImplementedError('pipeline type: {pipeline_type} does not exist')