import base64
import os
import sys
from pathlib import Path
from typing import List, Dict, Union, Tuple, Any
from bs4 import BeautifulSoup

from docx import Document

def _parse_html(file_path:str):
    """helper function to parse a single html file and add elements separated by 'p' tag into list
    
    also extracts 'p' ids in list

    parameters:
        file: Path to an html file

    returns: 
        Tuple containing list of html file text and id of each 'p' element
    """
    full_text = []
    full_ids = []
    doc_content = {}
    with open(file_path, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser') 
        for item in soup.find_all('p'): 
            text = item.getText()
            full_text.append(text)
            #id = item['id'] if item.has_attr('id') else None
            full_ids.append(id)
    doc_content['text'] = full_text
   # doc_content['text_id'] = full_ids
    return doc_content

def _parse_docx(file_path: str):
    """
    Receives a docx file and returns a lists of dicts containing parsed data.
    Note:
        Does not grab text below image objects. Text that says something similar to "This is what this image is about"
    :param file_path: URI of file
    :return: List of dicts containing paragraphs, images, and table objects.
    """
    try:
        doc = Document(file_path)
    except Exception as e:
        raise e

    # Contains all parsed components of the file
    doc_contents = {}

    # Grabs all "paragraphs". If you look in the outline of the said document, this is what will be returned here.
    text_list = [paragraph.text for paragraph in doc.paragraphs
                      if (any(len(run_text.text.strip()) != 0 for run_text in paragraph.runs))]

    doc_contents['text'] = text_list

    return doc_contents

def _parse_pdf(file_path: str):
    print("Importing parser from the tika library")
    # Tika's parser only imports if the tika.log file (which is located at /tmp/tika.log by default) exists
    # Import moved here since this function will only run if TIKA is actually running
    # https://github.com/chrismattmann/tika-python/issues/150
    from tika import parser
    
    print("Sending the content to tika to be parsed")
    r = parser.from_file(str(file_path), serverEndpoint='http://tika:9998')['content']

    # Construct the doc contents to return
    doc_contents = {
        'text': [i.replace('\n', ' ') for i in r.split('\n\n') if i != '']
    }

    return doc_contents

class FileExtractor:
    def __init__(self, 
                 docx_parser=_parse_docx, 
                 pdf_parser = _parse_pdf,
                 html_parser = _parse_html):
        self.docx_parser = docx_parser
        self.pdf_parser = pdf_parser
        self.html_parser = html_parser

    def parse_file(self,
        file_path: str,
    ) -> Tuple[Union[List[Dict[Union[int, Tuple[int, int, int]], str]], list, dict], str]:
        # identifies which type of input we are getting and executes the correct parsing
        # Should return a list of dictionaries.  Each dictionary will have integer 'index' and str 'text'.
        # Grabs extension less the period at the start
        file_type = Path(file_path).suffix[1:]
        if file_type == 'docx':
            return self.docx_parser(file_path), file_type
        elif file_type == 'pdf':
            return self.pdf_parser(file_path), file_type
        elif file_type == 'html':
            return self.html_parser(file_path), file_type
        else:
            raise TypeError(
                f"The filetype passed to get_paragraphs '{file_type}' is an unsupported file type. "
                f"Supported file types are 'docx', 'pdf', and 'pptx'."
            )
