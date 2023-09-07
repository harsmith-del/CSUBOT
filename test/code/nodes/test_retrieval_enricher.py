import os
import sys

import pytest
from haystack.schema import Document
from haystack.document_stores import ElasticsearchDocumentStore

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from nodes import RetrievalEnricher
from extractor import DOCExtractorDefault, Fragment
from indexer import DOCIndexer

test_index = 'test_index_retrieval'
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


def test_find_next_section(document_store):
    indexer = DOCIndexer(document_store)
    document_store.delete_index(index=test_index)
    fragments = [
        Fragment(text='First Sentence.', uuid=0, metadata = {'document':'test.txt'}),
        Fragment(text='Second Sentence.', uuid=1, metadata = {'document':'test.txt'}),
        Fragment(text='Third Sentence.', uuid=2, metadata = {'document':'test.txt'}),
    ] 
    indexer.add(fragments)
    store_docs = document_store.get_all_documents(index=test_index)
    
    enricher = RetrievalEnricher(
        document_store, 
        mode ='next_document'
        )
    cur_doc = store_docs[0]
    next_doc = enricher.find_next_section(cur_doc)
    assert store_docs[1] == next_doc[0]


def test_run(document_store):
    document_store.delete_index(index=test_index)
    indexer = DOCIndexer(document_store)
    extractor = DOCExtractorDefault(
        name='test_doc',
        dir=data_loc, 
        context_loc=f'{data_loc}/context/context.json',
        fragment_to_context_loc=f'{data_loc}/context/fragment_context_connector.json'
        )
    indexer.add(extractor.get_fragments())
    enricher = RetrievalEnricher(
        document_store, 
        mode ='next_document'
        )

    with open('/usr/src/test/data/document_example.json','r') as f:
        text = f.read()
        document = Document.from_json(data=text)
        
    result, _ = enricher.run([document])
    retrieved_doc = result['documents'][0]
    retrieved_id = retrieved_doc.meta['id']
    expected_id = 'FAR_1_102_2__d13e46'
    assert retrieved_id == expected_id