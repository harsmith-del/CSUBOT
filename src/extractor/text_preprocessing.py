import os
import re
import unicodedata
import string
from abc import ABC, abstractmethod
from typing import Union, List, Any, Dict, Tuple

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

nltk_data_path = os.environ['NLTK_DATA']
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt',download_dir = nltk_data_path)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords',download_dir = nltk_data_path)


stop_words = set(stopwords.words('english'))

class Preprocessor(ABC):
    """general idea is we have a generic preprocessor that can 
    transform and/or filter text
    this isn't fully functional yet - need to think about how to deal 
    with string sentences vs. list of words for example 
    """
    @abstractmethod
    def transform(self, text: str) -> str:
        pass

    @abstractmethod
    def filter(self, text: str) -> bool:
        pass

class clean_whitespace(Preprocessor):
    """cleans whitespace by converting newlines to spaces
    and multiple spaces to single spaces"""
    def transform(self, text: str)-> str:
        text = text.replace('\n',' ')
        text = re.sub('\s{2,}', ' ', text)
        return text
    
    def filter(self, text: str) -> bool:
        return True 
    
class remove_stopwords(Preprocessor):
    """removes stopwords from a string
    
    stopwords are globally defined in this file - consider changing
    """
    def transform(self, text: str)-> str:
        text = text.split()
        text =  ' '.join([word for word in text if word not in stop_words])
        return text
    
    def filter(self, text: str) -> bool:
        return True 
    
class remove_numbers(Preprocessor):
    """remove numbers from a string"""
    def transform(self, text: str)-> str:
        text = text.split()
        re_num = re.compile('\d+')
        text = ' '.join([word for word in text if not re_num.match(word)])
        return text
    def filter(self, text: str) -> bool:
        return True 
    
class remove_punctuation(Preprocessor):
    """remove punctuation from a string"""
    def __init__(self):
        self.trans_map = str.maketrans('', '', string.punctuation)

    def transform(self, text: str)-> str:
        return text.translate(self.trans_map)
    
    def filter(self, text: str) -> bool:
        return True 
    
class remove_blanklines(Preprocessor):
    """filter to remove blanklines"""
    def transform(self, text: str)-> str:
        return text
    
    def filter(self, text: str) -> bool:
        if (text == '' or  text.isspace()):
            return False
        return True 
    
# class tokens_to_string(Preprocessor):
#     """converts list of tokens to a string
#     each token is seperated 
#     """
#     def transform(self, tokens):
#         return ' '.join(tokens)
    
#     def filter(self, text):
#         return True 
    
# class tokenizer(Preprocessor):
#     """tokenizes a string"""
#     def transform(self, text):
#         return word_tokenize(text)
    
#     def filter(self, text):
#         return True 
    
class unicode_normalization(Preprocessor):
    """unicode normalization of a string using NFKD strategy
    """
    def transform(self, text: str)-> str:
        return unicodedata.normalize('NFKD', text)

    def filter(self, text: str) -> bool:
        return True
    
class lower_case(Preprocessor):
    """convert a string to all lowercase"""
    def transform(self, text: str)-> str:
        return text.lower()

    def filter(self, text: str)  -> bool:
        return True

"""_registry maps string to Preprocessor objects """
_registry = {
            'clean_whitespace' : clean_whitespace(),
            'remove_stopwords': remove_stopwords(),
            'remove_numbers': remove_numbers(),
            'remove_punctuation': remove_punctuation(),
            'unicode_normalize': unicode_normalization(),
            'lower_case': lower_case(),
            'remove_blanklines': remove_blanklines(), 
            }

def preprocessing_pipeline(text: List[str], functions: List[str])-> List[str]:
    """text preprocessing pipeline composed of sequence of Preprocessor objects
    
        paramaters:
            functions: list of str corresponding to ordered application of Preprocessors 
    """
    _functions = [_registry[f] for f in functions]
    #internally augment list so we can return which elements of the original list have been retained
    text_aug = [(i, p) for i, p in enumerate(text)]
    for func in _functions:
        text_aug =[(i, func.transform(p)) for  i, p in text_aug if func.filter(p)]
    
    text_processed = [p for i, p in text_aug]
    retained_indices = [i for i,p in text_aug]
    return text_processed, retained_indices