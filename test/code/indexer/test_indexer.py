import os
import sys

import pytest
from haystack.document_stores import ElasticsearchDocumentStore
from haystack.nodes import EmbeddingRetriever

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import DOCExtractorDefault, Fragment
from indexer import DOCIndexer

test_index = 'test_index_indexer'
data_loc = '/usr/src/test/data'

@pytest.fixture
def extractor():
    return DOCExtractorDefault(
        name=test_index,
        dir=data_loc, 
        context_loc=f'{data_loc}/context/context.json',
        fragment_to_context_loc=f'{data_loc}/context/fragment_context_connector.json'
        )

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


def test_enrich_metadata(document_store):
    indexer = DOCIndexer(document_store)
    fragments = [
        Fragment(text='First Sentence.', uuid=0, metadata = {'document':'test.txt'}),
        Fragment(text='Second Sentence.', uuid=1, metadata = {'document':'test.txt'}),
        Fragment(text='Third Sentence.', uuid=2, metadata = {'document':'test.txt'}),
    ] 
    fragments = indexer.enrich_metadata(fragments = fragments)
    expected = {
                0:{'prev':None,'next':1},
                1:{'prev':0,'next':2},
                2:{'prev':1,'next':None}
                }
    for index in expected:
        assert fragments[index].metadata['prev'] == expected[index]['prev']
        assert fragments[index].metadata['next'] == expected[index]['next']


def test_paragraphs_to_documents(document_store):
    indexer = DOCIndexer(document_store)
    fragments = [
        Fragment(text='a', uuid=0, 
                 metadata = {'document':'doc_0', 'prev':None,'next':1}),
        Fragment(text='b', uuid=1, 
                 metadata = {'document':'doc_1', 'prev':0,'next':2}),
        Fragment(text='c', uuid=2, 
                 metadata = {'document':'doc_2', 'prev':1,'next':None}),
    ] 
    docs = indexer.fragments_to_documents(fragments=fragments)
    expected_docs = [
        {'content':'a', 'meta':{'file':'doc_0','uuid':0,'prev':None,'next':1}},
        {'content':'b', 'meta':{'file':'doc_1','uuid':1,'prev':0,'next':2}},
        {'content':'c', 'meta':{'file':'doc_2','uuid':2,'prev':1,'next':None}},
    ]
    assert docs == expected_docs


def test_add(document_store):
    indexer = DOCIndexer(document_store)
    document_store.delete_index(index=test_index)
    with pytest.raises(Exception):
        store_docs = document_store.get_all_documents(index=test_index)
    
    empty_extractor = DOCExtractorDefault(
        name=test_index,
        dir=None,
        )
    empty_extractor.fragments = [
        Fragment(text='a', uuid=0, 
                 metadata = {'document':'doc_0'}),
        Fragment(text='b', uuid=1, 
                 metadata = {'document':'doc_1'}),
        Fragment(text='c', uuid=2, 
                 metadata = {'document':'doc_2'}),
    ] 
    indexer.add(empty_extractor.get_fragments())
    store_docs = document_store.get_all_documents(index=test_index)
    
    assert store_docs[0].content == 'a'
    assert store_docs[1].content == 'b'
    assert store_docs[2].content == 'c'
    assert all([store_docs[0].meta['file'] == 'doc_0', store_docs[0].meta['prev']==None, store_docs[0].meta['uuid']==0, store_docs[0].meta['next']==1])
    assert all([store_docs[1].meta['file'] == 'doc_1', store_docs[1].meta['prev']==0, store_docs[1].meta['uuid']==1, store_docs[1].meta['next']==2])
    assert all([store_docs[2].meta['file'] == 'doc_2', store_docs[2].meta['prev']==1, store_docs[2].meta['uuid']==2, store_docs[2].meta['next']==None])

    document_store.delete_index(index=test_index)


def test_indexer(extractor, document_store):
    document_store.delete_all_documents()
    indexer = DOCIndexer(document_store)
    indexer.add(extractor.get_fragments())
    
    query = {
            "match" : {
                "uuid" : 10
                }
            }
    retriever = EmbeddingRetriever(
                document_store=document_store,
                embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
                model_format="sentence_transformers",
                use_gpu=True,
            )
    document_store.update_embeddings(retriever)
    result = document_store.client.search(index=test_index, query=query)
    hit_docs = [document_store._convert_es_hit_to_document(hit) for hit in result["hits"]["hits"]]
    content = hit_docs[0].content

    expected_result = '(5) the government will maximize its use of commercial products and commercial services in meeting government requirements.'
    assert content == expected_result