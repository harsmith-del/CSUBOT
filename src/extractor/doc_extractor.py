import os 
import sys
from pathlib import Path
from typing import Union, List, Tuple, Dict, Callable
import json
import uuid

from .text_preprocessing import preprocessing_pipeline
from .file_extractor import FileExtractor

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from util.vars import CONTEXT, FRAGMENT_TO_CONTEXT

class Fragment:
    """represents the smallest subsection of a document
    
    params:
        text: text of the fragment from the documennt
        uuid: alphanumeric identifier
        metatdata: dictionary of metadata
    """
    def __init__(self, text: str, uuid =None, metadata: Dict=None):
        self.text = text
        self.uuid = uuid
        self.metadata = metadata

class DOCExtractorBase:
    """Extracts paragraphs from DOC documents for indexing
    
    we concieve of a single 'document' potentially being composed
    of multiple files all stored within a folder.
    this class operates on each file and aggregates them into a single
    entity. operations which must respect file boundaries should be conducted
    within the "Extractor" module. Operations on the whole document and those 
    related to ingestion into the document store should be performed in the Indexer.
    """

    def __init__(self, 
                 dir: Union[str, Path] = None,
                 file_extractor = None,
                 file_types: List[str] = ["html", "docx", "pdf"],
                 ):
        """constructor - all action is initiated by constructor 
        
        parameters:
            dir: str specifiying path to folder containing DOC html files 
            file_extractor: optional custom file parser
            file_types: file extensions handled by the file_extractor
        """
        self.fragments = []
        self.uuid = 0
        self.dir = dir
        if file_extractor is None:
            self.file_extractor = FileExtractor()
        else:
            self.file_extractor = file_extractor
        self.file_types = file_types

        self.__post_init__()

    def __post_init__(self):
        if self.dir is not None:
            self.load(self.dir)

    def load(self,                  
             dir: Union[str, Path],
            ):
        """loads and parses DOC data from folder

        parameters:
            dir: str specifiying path to folder containing specific document files
            file_type: str specifying file type of files to extract
        """
        files = []
        for ext in self.file_types:
            files.extend(Path(dir).glob(f'*.{ext}'))
        files = sorted(files)

        for file in files:
            file_content, _ = self.file_extractor.parse_file(file)
            fragments = self.generate_fragments(file, file_content)
            self.fragments.extend(fragments)

            self.file_level_operations(file_name = file,
                                       file_content = file_content,
                                       fragments=fragments)

        self.document_level_operations()

    def file_level_operations(self, file_name, file_content, fragments):
        """method for any work that needs to be done at the file level"""
        pass

    def document_level_operations(self,):
        """method for any work that needs to be done at the whole document level
        ideally most such work would be done in the indexer
        """
        pass

    def generate_fragments(self, file_name: str, file_content: Dict, min_char_length: int = 60):
        """generate fragments, the smallest portion of the document that will be indexed
        
        params:
            file_name: name of file parsed
            file_content: text content of file as strings, field ['text] contains list of str
            min_char_length: minimum character length of a fragment
        """
        fragments = self.paragraphs_to_fragments(file_content, min_char_length = min_char_length)
        fragments = self.assign_fragment_uuids(fragments)
        fragments = self.assign_fragment_metadata(fragments, file_name)
        return fragments

    def paragraphs_to_fragments(self, 
                                file_content: Dict, 
                                min_char_length: int = 60) -> List[Fragment]:
        """converts paragraphs - unit of extraction from files - into fragments
        
        this implementation splits on strings and ensures min character length
        params:
            file_content: text content of file as strings, field ['text] contains list of str
            min_char_length: minimum character length of a fragment
        """
        paragraphs = file_content['text']
        all_sentences = ''.join(paragraphs).split('.')
        fragments = []
        curr_sentence = ''
        for sentence in all_sentences:
            curr_sentence += sentence + '.'
            if len(curr_sentence) >= min_char_length and ' ' in curr_sentence:
                fragments.append(Fragment(text=curr_sentence))
                curr_sentence = ''

        return fragments
    
    def assign_fragment_uuids(self, fragments: List[Fragment]) -> List[Fragment]:
        """assign uuids to fragments"""
        for fragment in fragments:
            fragment.uuid = self.uuid
            self.uuid = self.uuid + 1
        return fragments
    
    def assign_fragment_metadata(self, fragments: List[Fragment],
                                 file_name: str) -> List[Fragment]:
        """assign metatdata to fragments"""
        for fragment in fragments:
            _tmp ={
                    'document' :str(file_name), 
                }
            fragment.metadata = _tmp
        return fragments

    def get_fragments(self) -> List[Fragment]:
        return self.fragments

class DOCExtractorDefault(DOCExtractorBase):
    """Default Document Extractor, alternatives can be implemented if required"""
    def __init__(self, 
                 name: str = 'default',
                 dir: Union[str, Path] = None,
                 file_extractor: Callable = None,
                 file_types: List[str] = ["html", "docx", "pdf"],
                 context_loc: str =  CONTEXT,
                 fragment_to_context_loc: str = FRAGMENT_TO_CONTEXT, 
                 ):
        """constructor - all action is initiated by constructor 
        
        parameters:
            name: name of the document
            dir: str specifiying path to folder containing DOC html files 
            file_extractor: optional custom file parser
            file_types: file extensions handled by the file_extractor
            context_loc: path to store context data
            fragment_to_context_loc: path to store fragment to context mapping
        """
        self.name = name
        self.context_loc = context_loc.format(document=name)
        self.fragment_to_context_loc = fragment_to_context_loc.format(document=name)
        self.context = {}
        self.fragment_to_context = {}
        super().__init__(
                 dir=dir,
                 file_extractor = file_extractor,
                 file_types = file_types,
                 )

    def __post_init__(self,):
        context_dir = Path(self.context_loc).parents[0]
        context_dir.mkdir(exist_ok=True, parents=True)
        map_dir = Path(self.fragment_to_context_loc).parents[0]
        map_dir.mkdir(exist_ok=True, parents=True)
        super().__post_init__()
        
    def file_level_operations(self,
                              file_name: str,
                              file_content,
                              fragments: List[Fragment]):
        """ file level operations

        creates fragment context for fragments in this file
        params:
            file_name: name of file parsed
            file_content: text content of file as strings, field ['text] contains list of str
            fragments: fragments from this file
        """
        fragment_to_context, context = self.fragment_to_context_connector(fragments=fragments,
                                                        context_length=4)
        self.context.update(context)
        self.fragment_to_context.update(fragment_to_context)

    def document_level_operations(self,):
        self.write_fragment_context_connector()

    def fragment_to_context_connector(self, 
                                      fragments: List[Fragment], 
                                      context_length: int = 4) -> Tuple[Dict, Dict]:
        """creates context around each fragment
        
        context is generated from adjacent fragaments. 
        params:
            fragments: fragments for which context is generated
            context_length: lenght of context in number of fragments
        returns:
            fragment_to_context: maps from fragment id to context id
            context: dictionary of context id to context text
        """
        fragment_to_context = {}
        context = {}
        counter = 0
        _uuid = str(uuid.uuid4())
        curr_context = ""
        for i, fragment in enumerate(fragments):
            # If at end of self.paragraphs, then we will combine last element with curr_context instead of creating two separate contexts
            if (counter >= context_length) and (i < len(fragments)-1):
                context[_uuid] =  curr_context
                curr_context = ""
                _uuid = str(uuid.uuid4())
                counter = 0
            fragment_to_context[fragment.uuid] = _uuid
            curr_context = curr_context + fragment.text
            counter += 1
        context[_uuid] =  curr_context
        return fragment_to_context, context

    def write_fragment_context_connector(self,):
        """write newly created self.context and self.sentence_to_context_connector
        to json to be referenced when pulling longer context
        from retrieved documents
        """
        with open(self.fragment_to_context_loc, 'w') as fp:
            json.dump(self.fragment_to_context, fp)

        cleaning_pipeline = [
            'unicode_normalize',
            'clean_whitespace',
            'remove_blanklines',
            ]
        
        keys = list(self.context.keys())
        values = list(self.context.values())
        text_cleaned, indices = preprocessing_pipeline(values, cleaning_pipeline)
        self.context = {keys[i]:p  for i,p in zip(indices, text_cleaned) }
        with open(self.context_loc, 'w') as fp:
            json.dump(self.context, fp)
    