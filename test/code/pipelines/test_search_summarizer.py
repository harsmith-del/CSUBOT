import os
import sys
import json

import pytest
from haystack.document_stores import ElasticsearchDocumentStore
from haystack import Document

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import DOCExtractorDefault
from indexer import DOCIndexer, build_index
from pipelines import SearchSummarizer
from util import CONTEXT, FRAGMENT_TO_CONTEXT
test_index = 'test_index'
data_loc = '/usr/src/test/data'

@pytest.fixture
def document_store():

    build_index(doc_name=test_index, 
                data_path = data_loc, 
                ds_path = '/tmp/data', 
                retriever  ='Embedding', 
                docstore_type = 'elasticsearch')
    
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
def summarizer(document_store):
    default_retriever = 'Embedding'
    default_enricher = 'next_document'
    default_summarizer = 'local'
    f = open(f'{data_loc}/context/context.json')
    context_list = json.load(f)
    f = open(f'{data_loc}/context/sentence_context_connector.json')
    sentence_context_dict = json.load(f)
    sentence_context_dict = {int(k):v for k,v in sentence_context_dict.items()}
    
    return SearchSummarizer(
        document_store = document_store, 
        summarizer=default_summarizer,
        retriever=default_retriever,
        enricher=default_enricher,
        sentence_context_connector=sentence_context_dict,
        context_store=context_list,)


def test_run(document_store):
    context_loc=CONTEXT.format(document=test_index)
    fragment_to_context_loc = FRAGMENT_TO_CONTEXT.format(document=test_index)
    f = open(context_loc)
    context_list = json.load(f)
    f = open(fragment_to_context_loc)
    sentence_context_dict = json.load(f)
    sentence_context_dict = {int(k):v for k,v in sentence_context_dict.items()}
    summarizer = SearchSummarizer(
        document_store=document_store, 
        retriever='Embedding', 
        sentence_context_connector=sentence_context_dict,
        context_store=context_list,
        )

    query = 'what is the far?'
    _, (summary, retrieved_docs) = summarizer.run(query)
    expected_summary = '202(a)(11) or other appropriate exemptions in 5.202; (5) the contractor does not have an active exclusion record in the system for award management (see far 9); (6) it is the policy of the system to promote competition in the acquisition process. if a contractor is exempt from disclosure under the freedom of information act (5 u.s.), he or she must notify the far system as soon as possible. the contractor must notify far within 30 days of the award of the contract containing the option'
    assert expected_summary == summary
    assert len(retrieved_docs) == 5


def test_prepare_response(summarizer):
    summary = 'summary'
    retrieved_docs_dict = [
        {
            'content': 'a',
            'meta': {'file': '/home/jackye/Documents/mf-FARbot/data/FAR_dita_html/1.000.html'},
            'score': '1',
        },
        {
            'content': 'b',
            'meta': {'file': 'path_b'},
            'score': '2',
        }
    ]
    retrieved_docs = [Document.from_dict(doc) for doc in retrieved_docs_dict]
    result_from_summarizer = (summary, retrieved_docs)
    
    prepared_responses = summarizer.prepare_response(result_from_summarizer)
    assert prepared_responses['summary'] == summary
    
    expected_prepared_docs = [
        {
            'score':1.0,
            'content':'a',
        },
        {
            'score':2.0,
            'content':'b',
        },
    ]
    assert expected_prepared_docs[0]['score'] == prepared_responses['relevant_docs'][0]['score']
    assert expected_prepared_docs[1]['score'] == prepared_responses['relevant_docs'][1]['score']
    assert expected_prepared_docs[0]['content'] == prepared_responses['relevant_docs'][0]['content']
    assert expected_prepared_docs[1]['content'] == prepared_responses['relevant_docs'][1]['content']