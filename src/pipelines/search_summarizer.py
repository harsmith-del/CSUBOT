import os
import sys
from pathlib import Path
from typing import Dict, Tuple, List

from typing import Dict, List, Optional, Tuple, Union, Any

from haystack import Pipeline
from haystack.nodes import BM25Retriever, EmbeddingRetriever, \
    TfidfRetriever, SentenceTransformersRanker,\
    TransformersSummarizer, DocumentMerger, JoinDocuments

from haystack.nodes import  PromptNode, PromptTemplate, PromptModel
from haystack.nodes.prompt.shapers import AnswerParser
from haystack.document_stores import BaseDocumentStore
from haystack.schema import Document

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from nodes import RetrievalEnricher, PromptNodeWrapped
from util import connect_to_docstore
from util.vars import EMBEDDING_MODEL, EMBEDDING_MODEL_FORMAT


class SearchSummarizer:
    """pipeline for query-based search, document retrival, and summarization of results"""

    def __init__(self,
                 document_store: BaseDocumentStore,  
                 retriever: str = 'Embedding', 
                 summarizer: str = 'local',
                 enricher: str = None,
                 sentence_context_connector: dict = None,
                 context_store: list = None,
                 ) -> None:
        """construtor
        
        parameters:
            document_store: Haystack DocumentStore, document database to search
            retriever: str, specifies type of Haystack Retriever used to search document store
            enricher: str, specifies type of RetrievalEnricher to use
            sentence_context_connector: dict, dictionary to convert from the sentence uuid to context uuid/index
            context_store: list, contains list of all full length context to match with each sentence
        """

        self.pipeline = None
        self.retriever = None
        self.document_store = document_store
        self.enricher = enricher
        self.sentence_context_connector = sentence_context_connector
        self.context_store = context_store

        self.__post_init__(summarizer, retriever)

    
    def __post_init__(self, 
                      summarizer: str,
                      retriever: str, ) -> None:
        """actions to initialize pipeline object
        
        parameters:
            retriever: str, specifies type of Haystack Retriever
            update_embeddings: bool, indicating whether to updated document store embeddings
        """
        print('in pipeline post init')
        if retriever == 'BM25':
           self.retriever = BM25Retriever(self.document_store)
        
        elif retriever == 'TfIdf':
           self.retriever = TfidfRetriever(document_store=self.document_store)

        elif retriever == 'Embedding':
            print('setting up embedding retriever')
            self.retriever = EmbeddingRetriever(
                document_store=self.document_store,
                embedding_model=EMBEDDING_MODEL,
                model_format=EMBEDDING_MODEL_FORMAT,
                use_gpu=True,
            )
        else:
            raise NotImplementedError(f'retriever type {retriever} has not been implemented')

        print('setting up sentence transformer ranker')
        ranker = SentenceTransformersRanker(model_name_or_path="cross-encoder/ms-marco-MiniLM-L-12-v2")
        enricher = RetrievalEnricher(self.document_store, mode =self.enricher)
        merger = DocumentMerger()

        # Use either open source or OpenAI model. For OpenAI, need API KEY placed into .env
        if summarizer == 'local':
            print('setting up sentence transformer summarizer')
            summarizer_node= TransformersSummarizer(model_name_or_path='t5-large', 
                                                    min_length=100, max_length=400,
                                                    use_gpu=True,
                                                    )
        elif summarizer == 'openai':
            print('setting up openai summarizer')
            try:
                API_KEY = os.environ["OPENAI_KEY"]
            except:
                raise('OpenAI API Key not found')
            
            custom_prompt = PromptTemplate(prompt="""Synthesize a comprehensive answer from the following topk most relevant paragraphs and the given question. 
                             Provide a clear and concise response that summarizes the key points and information presented in the paragraphs. 
                             You must only use information from the given documents.
                             If the documents do not contain the answer to the question, say that answering is not possible given the available information.
                             Your answer should be in your own words and be no longer than 50 words. 
                             \n\n Paragraphs: {join(documents)} \n\n Question: {query} \n\n Answer:""",
                             output_parser=AnswerParser(),) 

            summarizer_node = PromptNodeWrapped("text-davinci-003", default_prompt_template=custom_prompt, api_key=API_KEY)
        else:
            raise NotImplementedError(f'summarizer choice: {summarizer} not recognized')

        self.pipeline = Pipeline()
        self.pipeline.add_node(component=self.retriever, name='Retriever', inputs=['Query'])
        self.pipeline.add_node(component=ranker, name='Ranker', inputs=['Retriever'])
        self.pipeline.add_node(component=enricher, name='Enricher', inputs=['Ranker'])
        self.pipeline.add_node(component=merger, name='Merger', inputs=['Enricher'])
        self.pipeline.add_node(component=summarizer_node, name='Summarizer', inputs=['Merger'])
        self.pipeline.add_node(component=JoinDocuments(join_mode="concatenate"), name="JoinResults", inputs=["Summarizer", 'Enricher'])
        
    def run(self, 
            query: str, 
            params: Dict =None) -> Tuple[str, Tuple[str, List[Document]]]:
        """run pipeline
        
        parameters: 
            query: str, text query used to search DocumentStore
            params: dict, parameters to be passed to pipeline nodes
        return:
            tuple of pipeline type (probably not needed) and results
                results is a tuple of the summary and list of relevant documents
        """
        if params is None:
            params={
                "Retriever": {"top_k": 10},
                "Ranker": {"top_k": 5}
            }
        result = self.pipeline.run(query=query, params = params)
        summary = result['documents'][-1].meta['summary']
        relevant_docs = result['documents'][:-1]

        for doc in relevant_docs:
            doc.meta['extended_content'] = self.context_store[self.sentence_context_connector[doc.meta['uuid']]]

        results = (summary, relevant_docs)
        return 'summarizer', results
    
    def prepare_response(self, result):
        relevant_doc_data = []

        summary, relevant_docs = result
        for doc in relevant_docs:
            temp = {
                    'meta': doc.meta,
                    'score': doc.score,
                    'content': doc.content
                    }
            relevant_doc_data.append(temp)

        return {'summary': summary, 'relevant_docs': relevant_doc_data}
