import os
import sys

import pytest
from haystack.document_stores import ElasticsearchDocumentStore

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import DOCExtractorDefault
from util import util_funcs

test_index = 'test_index'
data_loc = '/usr/src/test/data'

@pytest.fixture
def extractor():
    return DOCExtractorDefault(
        data_loc, 
        context_loc=f'{data_loc}/context.json',
        sentence_to_context_loc=f'{data_loc}/sentence_context_connector.json'
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


def test_connect_to_docstore(document_store):
    connected_document_store = util_funcs.connect_to_docstore(
        docstore_type='elasticsearch',
        retriever='Embedding',
        index=test_index,
        )
    assert connected_document_store.type == document_store.type
    assert connected_document_store.index == document_store.index
    assert connected_document_store.embedding_field == document_store.embedding_field