import sys

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import preprocessing_pipeline

data_loc = '/usr/src/test/data'


def test_clean_whitespace():
    paragraph = ['a  b c']
    cleaning_pipeline = ['clean_whitespace']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = 'a b c'
    assert text == expected_text


def test_remove_stopwords():
    paragraph = ['Stopword: you']
    cleaning_pipeline = ['remove_stopwords']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = 'Stopword:'
    assert text == expected_text


def test_remove_numbers():
    paragraph = ['Number: 1']
    cleaning_pipeline = ['remove_numbers']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = 'Number:'
    assert text == expected_text


def test_remove_punctuation():
    paragraph = ['Punctuation: !']
    cleaning_pipeline = ['remove_punctuation']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = 'Punctuation '
    assert text == expected_text


def test_remove_blanklines():
    paragraph = [ ' ','test']
    cleaning_pipeline = ['remove_blanklines']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = 'test'
    assert text == expected_text


def test_unicode_normalization():
    paragraph = [' ']
    cleaning_pipeline = ['unicode_normalize']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = ' '
    assert text == expected_text


def test_lower_case():
    paragraph = ['TEST']
    cleaning_pipeline = ['lower_case']
    cleaned_paragraph, _ = preprocessing_pipeline(paragraph, cleaning_pipeline)
    text = cleaned_paragraph[0]
    
    expected_text = 'test'
    assert text == expected_text


def test_cleaning_pipeline():
    paragraphs = ['TEst  1', '  ', '  test2']
    cleaning_pipeline = [
        'unicode_normalize',
        'clean_whitespace',
        'lower_case',
        'remove_blanklines',
        ]
    paragraphs_cleaned, _ = preprocessing_pipeline(paragraphs, cleaning_pipeline)
    assert len(paragraphs_cleaned) == 2
    
    p0 = paragraphs_cleaned[0]
    p1 = paragraphs_cleaned[1]
    p_expected = ['test 1',' test2']
    assert p0 == p_expected[0]
    assert p1 == p_expected[1]