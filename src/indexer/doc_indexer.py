import os
import sys
from pathlib import Path
from typing import List, Dict

from haystack.nodes import PreProcessor
from haystack.document_stores import BaseDocumentStore

from loguru import logger

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import preprocessing_pipeline, Fragment

class DOCIndexer:
    """class that takes extracted document and indexes it into a document store"""

    def __init__(self, docstore: BaseDocumentStore,
                 split_len: int =100, 
                 split_overlap: int =20) -> None:
        """"initialize DOCIndexer
        
        parameters:
            docstore: haystack Document Store where indexed documents will be held
            split_len: int, max word length of "documents" - fragments can be split further
                if desired or split_len can be set to a high value to avoid further splitting 
            split_overlap: number of words to overlap between split documents
        """
        self.docstore = docstore
        self.cleaning_pipeline = ['unicode_normalize',
                    'clean_whitespace',
                    'lower_case',
                    'remove_blanklines',]
        
        self.preprocessor = PreProcessor(
                clean_whitespace=True,
                clean_header_footer=True,
                clean_empty_lines=True,
                split_by="word",
                split_length=split_len,
                split_overlap=split_overlap,
                split_respect_sentence_boundary=True,
            )
        
    def enrich_metadata(self, 
                        fragments: List[Fragment]) -> List[Fragment]:
        """enrich metadata by adding next and previous 
        document id to create implicit linked list
        
        parameters:
            metadata: list, metatdata associated with paragraphs 
            paragraphs: list of documents for indexing

        return: metadata, as augemented in this function
        """
        
        #handle edge cases
        key_0 = fragments[0].uuid
        key_1 = fragments[1].uuid
        key_end = fragments[-1].uuid
        key_endm1 = fragments[-2].uuid
        fragments[key_0].metadata['prev'] = None
        fragments[key_0].metadata['next'] = key_1
        fragments[key_end].metadata['prev'] = key_endm1
        fragments[key_end].metadata['next'] = None

        n_elms = len(fragments)
        for i in range(1,n_elms-1):
            key_i = fragments[i].uuid
            key_im1 = fragments[i-1].uuid
            key_ip1 = fragments[i+1].uuid
            fragments[key_i].metadata['prev'] = key_im1
            fragments[key_i].metadata['next'] = key_ip1

        return fragments

        
    def fragments_to_documents(self, 
                                fragments: List[Fragment]) -> List[Dict]:
        """convert extracted fragments to haystack documents and
        associated metadata

        parameters:
            fragments: list of fragments extracted from documents for indexing
            metadata: list of metadata associated with each paragraph

        return: list of documents
        """
        docs = []
        for f in fragments:
            m = f.metadata
            d = {
                "content" : f.text,
                "meta": {
                            "file": m["document"], 
                            "uuid" : f.uuid,
                            "prev" : m["prev"],
                            "next" : m["next"],
                        } 
                }
            docs.append(d)
        return docs
    
    def add(self, 
            fragments: List[Fragment]) -> None:
        """index documents by adding to document store
        
        converts extracted document into haystack format and augments metadata
        parameters: 
            doc_data: extracted document data
        """

        fragment_text = [f.text for f in fragments]
        fragment_text, _ = preprocessing_pipeline(fragment_text, self.cleaning_pipeline)
        for f, t in zip(fragments, fragment_text): f.text = t 
        fragments = self.enrich_metadata(fragments)
        document_docs = self.fragments_to_documents(fragments)

        docs_preprocessed = self.preprocessor.run_batch(document_docs)
        self.docstore.write_documents(docs_preprocessed[0]['documents'])