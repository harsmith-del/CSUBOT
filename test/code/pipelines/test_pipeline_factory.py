import os
import sys
import json

import pytest
from haystack.document_stores import ElasticsearchDocumentStore

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from pipelines import SearchSummarizer, pipeline_factory

test_index = 'test_index'
data_loc = '/usr/src/test/data'

@pytest.fixture
def document_store():
    container_prefix = os.environ['CONTAINER_PREFIX']
    es_host = f'{container_prefix}_es_haystack'
    document_store = ElasticsearchDocumentStore(
        host=es_host,
        username="",
        password="",
        index=test_index,
        similarity="dot_product",
        embedding_dim=768
    )
    return document_store

@pytest.fixture
def context_list():
    f = open(f'{data_loc}/context/context.json')
    context_list = json.load(f)
    return context_list


@pytest.fixture
def sentence_context_dict():
    f = open(f'{data_loc}/context/fragment_context_connector.json')
    sentence_context_dict = json.load(f)
    sentence_context_dict = {int(k):v for k,v in sentence_context_dict.items()}
    return sentence_context_dict


@pytest.fixture
def summarizer(document_store, context_list, sentence_context_dict):
    default_retriever = 'Embedding'
    default_enricher = 'next_document'
    default_summarizer = 'local'
    
    return SearchSummarizer(
        document_store = document_store, 
        summarizer=default_summarizer,
        retriever=default_retriever,
        enricher=default_enricher,
        sentence_context_connector=sentence_context_dict,
        context_store=context_list,)


def test_pipeline_factory(document_store, summarizer, context_list, sentence_context_dict):
    pipeline = 'summarization'
    pipeline_summarizer = pipeline_factory(
        pipeline_type = pipeline,
        document_store = document_store, 
        summarizer='local',
        retriever='Embedding',
        enricher='next_document',
        sentence_context_connector=sentence_context_dict,
        context_store=context_list,
        )
    
    assert summarizer.pipeline.components.keys() == pipeline_summarizer.pipeline.components.keys()
    assert summarizer.retriever.embedding_model == pipeline_summarizer.retriever.embedding_model
    assert summarizer.document_store == pipeline_summarizer.document_store
    assert summarizer.enricher == pipeline_summarizer.enricher
    assert summarizer.sentence_context_connector == pipeline_summarizer.sentence_context_connector
    assert summarizer.context_store == pipeline_summarizer.context_store