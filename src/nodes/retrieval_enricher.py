from typing import Optional, List, Dict, Tuple

from haystack.nodes.base import BaseComponent
from haystack.nodes import DocumentMerger
from haystack.schema import Document
from haystack.document_stores import BaseDocumentStore

class RetrievalEnricher(BaseComponent):
    """add additional potentially relevant documents to retrieval results"""
    outgoing_edges = 1

    def __init__(self, 
                 document_store: BaseDocumentStore,
                 mode: str =None) -> None:
        """constructor
        
        parameters: 
            document_store: Haystack DocumentStore with documents to enrich retrival
            mode: str (should be list of enum), enrichment activity (currenly only option is next_document)
        """
        self.document_store = document_store
        self.mode = mode
        self.merger = DocumentMerger()

    def find_next_section(self, 
                          doc: Document) -> Document:
        """enrich retrieved documents by adding the next section
        
        parameters:
            doc: Haystack Document, focal document, 
                section following this document will be returned

        returns: Haystack Document, next_doc, document following 'doc'
        """

        split_target =  doc.meta['_split_id'] + 1
        next_uuid = doc.meta['next']
        filter = {"$and":
                        {
                            "uuid" : {"$eq" : doc.meta['uuid']},
                            "_split_id" : {"$eq" : split_target},
                        }
                }
        next_doc = self.document_store.get_all_documents(filters=filter)

        if next_doc == [] and next_uuid is not None:  
            #no hits found in next split, try next uuid
            filter = {"$and":
                            {
                                "uuid" : {"$eq" : next_uuid},
                                "_split_id" : {"$eq" : 0},
                            }
                    }
            filter = {"uuid": {"$eq":next_uuid}}
            next_doc = self.document_store.get_all_documents(filters=filter)

        return next_doc

    def run(self, 
            documents: List[Document]) -> Tuple[Dict, str]:
        """run function matching Haystack API for a node
        
        parameters: 
            documents: List[Document], documents to be enriched
        returns: 
            output: enriched documents 
        """
        enriched_documents = []
        for doc in documents:
            if self.mode == 'next_document':  #convert to enum
                hit_docs = self.find_next_section(doc)
                doc_enriched = self.merger.merge(documents=[doc, *hit_docs])[0]
                doc_enriched.score = doc.score
                doc_enriched.meta = doc.meta
                enriched_documents.append(doc_enriched)
            else: 
                enriched_documents.append(doc)

        output={
            "documents": enriched_documents,
        }
        return output, "output_1"

    def run_batch(self, queries: List[str], my_arg: Optional[int] = 10):
        # Insert code here to manipulate the input and produce an output dictionary
        raise NotImplementedError('run_batch has not yet been implemented for Retrival Enricher')
        