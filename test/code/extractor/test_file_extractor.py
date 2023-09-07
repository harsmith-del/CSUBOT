import sys

import pytest

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import file_extractor

data_loc = '/usr/src/test/data'

@pytest.fixture
def file_extractor_obj():
    return file_extractor.FileExtractor()

def test_html_get_paragraphs(file_extractor_obj):
    expected_result = {
        'text': [
            'Document Title',
            'A plain paragraph having some bold and some italic.',
            'Intense quote',
            'first item in unordered list',
            'first item in\nordered list',
            'Qty',
            'Id',
            'Desc',
            '\xa0'
            ],
        }

    r, t = file_extractor_obj.parse_file(f'{data_loc}/demo.html')
    assert r == expected_result
    assert t == 'html'


def test_docx_get_paragraphs(file_extractor_obj):
    expected_result = {
        'text': [
            'Document Title',
            'A plain paragraph having some bold and some italic.',
            'Intense quote',
            'first item in unordered list',
            'first item in ordered list'
            ],
        }

    r, t = file_extractor_obj.parse_file(f'{data_loc}/demo.docx')
    assert r == expected_result
    assert t == 'docx'