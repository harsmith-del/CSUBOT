import os
import sys
from pathlib import Path
from typing import Dict, Tuple

from haystack import Pipeline
from haystack.nodes import BM25Retriever, EmbeddingRetriever, \
    DensePassageRetriever, TfidfRetriever, \
     SentenceTransformersRanker, FARMReader
from haystack.document_stores import BaseDocumentStore

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from nodes import RetrievalEnricher

class SearchQA:
    """pipeline for query-based search, document retrival, and question answering"""
    def __init__(self, 
                 document_store: BaseDocumentStore,  
                 retriever: str = 'Embedding', 
                 enricher: str = None) -> None:
        """construtor
        
        parameters:
            document_store: Haystack DocumentStore, document database to search
            retriever: str, specifies type of Haystack Retriever used to search document store
            enricher: str, specifies type of RetrievalEnricher to use
        """

        self.pipeline = None
        self.retriever = None
        self.document_store = document_store
        self.enricher = enricher

        self.__post_init__(retriever)

    
    def __post_init__(self, 
                      retriever: str, 
                      update_embedding: str) -> None:
        """actions to initialize pipeline object
        
        parameters:
            retriever: str, specifies type of Haystack Retriever
            update_embeddings: bool, indicating whether to updated document store embeddings
        """

        if retriever == 'BM25':
           self.retriever = BM25Retriever(self.document_store)

        elif retriever == 'TfIdf':
           self.retriever = TfidfRetriever(document_store=self.document_store)

        elif retriever == 'Embedding':
            self.retriever = EmbeddingRetriever(
                document_store=self.document_store,
                embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
                model_format="sentence_transformers",
                use_gpu=True,
            )

        elif retriever == 'DensePassage': 
            self.retriever = DensePassageRetriever(
                document_store=self.document_store,
                query_embedding_model="facebook/dpr-question_encoder-single-nq-base",
                passage_embedding_model="facebook/dpr-ctx_encoder-single-nq-base"
            )
        else:
            raise NotImplementedError(f'retriever type {retriever} has not been implemented')

        ranker = SentenceTransformersRanker(model_name_or_path="cross-encoder/ms-marco-MiniLM-L-12-v2")
        enricher = RetrievalEnricher(self.document_store, mode =self.enricher)
        reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)

        self.pipeline = Pipeline()
        self.pipeline.add_node(component=self.retriever, name='Retriever', inputs=['Query'])
        self.pipeline.add_node(component=ranker, name='Ranker', inputs=['Retriever'])
        self.pipeline.add_node(component=enricher, name='Enricher', inputs=['Ranker'])
        self.pipeline.add_node(component=reader, name='Reader', inputs=['Enricher'])
        
    def run(self, 
            query: str, 
            params: Dict =None) -> Tuple[str, Dict]:
        """run pipeline
        
        parameters: 
            query: str, text query used to search DocumentStore
            params: dict, parameters to be passed to pipeline nodes
        return:
            tuple of pipeline type (probably not needed) and results from QA pipeline
        """
        if params is None:
            params={
                "Retriever": {"top_k": 10},
                "Ranker": {"top_k": 5}
            }

        result = self.pipeline.run(query=query, params = params)
        return 'qa', result
    
    def prepare_response(self, result):
        return {'result': result}