import os
import sys
from pathlib import Path
import json

import pytest

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor import DOCExtractorDefault, Fragment

data_loc = '/usr/src/test/data'

@pytest.fixture
def sample_extractor():
    return DOCExtractorDefault(
        name='test_doc',
        dir=data_loc, 
        context_loc=f'{data_loc}/context/context.json',
        fragment_to_context_loc=f'{data_loc}/context/fragment_context_connector.json'
        )

@pytest.fixture
def empty_extractor():
    return DOCExtractorDefault(
        dir=None,
        )


def test_parse_file_sentence(empty_extractor):
    min_char_length = 50
    file_content, _ = empty_extractor.file_extractor.parse_file(f'{data_loc}/1.102-2.html')
    fragments = empty_extractor.generate_fragments(f'{data_loc}/1.102-2.html', file_content)

    assert len(fragments) == 32 
    assert all([len(fragment.text) >= min_char_length for fragment in fragments])
    assert all([' ' in fragment.text for fragment in fragments])

    assert fragments[-1].text == '\nIn attaining these goals, and in its overall operations, the process\nshall ensure the efficient use of public resources.'


@pytest.mark.parametrize("context_len, expected_context", [
    (2, ['First Sentence.Second Sentence.', 'Third Sentence.Fourth Sentence.']),
    (3, ['First Sentence.Second Sentence.Third Sentence.Fourth Sentence.'])
])
def test_create_sentence_to_context_connector(empty_extractor, context_len, expected_context):
    fragments = [
        Fragment(text='First Sentence.', uuid=0),
        Fragment(text='Second Sentence.', uuid=1),
        Fragment(text='Third Sentence.', uuid=2),
        Fragment(text='Fourth Sentence.', uuid=3),
    ] 
    fragment_to_context, context  = empty_extractor.fragment_to_context_connector(fragments=fragments,
                                                context_length=context_len)
    if context_len==2:
        assert context[fragment_to_context[0]] == expected_context[0]
        assert context[fragment_to_context[2]] == expected_context[1]
    elif context_len==3:
        assert context[fragment_to_context[0]] == expected_context[0]

def test_write_sentence_context_connector(empty_extractor):
    context_loc = f'{data_loc}/context/context_test.json'
    fragment_to_context_loc = f'{data_loc}/context/fragment_context_connector_test.json'
    empty_extractor.context = {'aaaa':'some text', 'bbbb':'different text'}
    empty_extractor.fragment_to_context = {'1':'aaaa','2':'bbbb'}
    empty_extractor.context_loc = context_loc
    empty_extractor.fragment_to_context_loc = fragment_to_context_loc
    empty_extractor.write_fragment_context_connector()

    f = open(context_loc)
    context = json.load(f)
    assert context == {'aaaa':'some text', 'bbbb':'different text'}

    f = open(fragment_to_context_loc)
    fragment_to_context = json.load(f)
    assert fragment_to_context == {'1':'aaaa','2':'bbbb'}

    os.remove(context_loc)
    os.remove(fragment_to_context_loc)


def test_load(empty_extractor):
    assert empty_extractor.fragments == []
    assert empty_extractor.context == {}
    assert empty_extractor.fragment_to_context == {}
    assert empty_extractor.uuid == 0
    
    context_loc = f'{data_loc}/context/context.json'
    fragment_to_context_loc = f'{data_loc}/context/fragment_context_connector.json'
    empty_extractor.context_loc = context_loc
    empty_extractor.fragment_to_context_loc = fragment_to_context_loc
    if os.path.exists(context_loc):
        os.remove(context_loc)
    if os.path.exists(fragment_to_context_loc):
        os.remove(fragment_to_context_loc)

    empty_extractor.load(
                    dir=data_loc, 
                )
    
    assert empty_extractor.fragments != []
    assert empty_extractor.context != {}
    assert empty_extractor.fragment_to_context != {}
    assert empty_extractor.uuid != 0
    assert Path(context_loc).exists()
    assert Path(fragment_to_context_loc).exists()

    os.remove(context_loc)
    os.remove(fragment_to_context_loc)


def test_extracted_paragraphs(sample_extractor):
    fragments = sample_extractor.fragments
    print('wait')
    p0 = fragments[0].text
    p1 = fragments[51].text
    p2 = fragments[95].text

    p_expected = ['This part sets forth basic policies and general information about the Federal Acquisition Regulations System including purpose, authority, applicability, issuance, arrangement, numbering, dissemination, implementation, supplementation, maintenance, administration, and deviation.',
                  ' The contractor shall not be reimbursed for costs of settlements with subcontractors unless required approvals or ratifications have been obtained (see 49.',
                  'e.,\tinstead of performance only by a self-employed individual).',
                  ]

    assert p0 == p_expected[0]
    assert p1 == p_expected[1]
    assert p2 == p_expected[2]


def test_extracted_metadata(sample_extractor):
    fragments = sample_extractor.fragments
    m0 = fragments[0].metadata['document']
    m1 = fragments[50].metadata['document']
    m2 = fragments[95].metadata['document']

    m_expected = [  
                    '/usr/src/test/data/1.000.html',
                    '/usr/src/test/data/49.304-3.html',
                    '/usr/src/test/data/52.203-16.html',
                  ]
    
    assert m0 == m_expected[0]
    assert m1 == m_expected[1]
    assert m2 == m_expected[2]

    assert all([fragment.metadata.keys() == {'document'} for fragment in fragments])


def test_fragment_to_context_connector(sample_extractor):
    context = sample_extractor.context
    fragment_to_context = sample_extractor.fragment_to_context
    context0 = context[fragment_to_context[0] ]
    context1 = context[fragment_to_context[56]]
    context2 = context[fragment_to_context[92]]

    context_expected = [
        'This part sets forth basic policies and general information about the Federal Acquisition Regulations System including purpose, authority, applicability, issuance, arrangement, numbering, dissemination, implementation, supplementation, maintenance, administration, and deviation. subparts 1.2,1.3, and 1.4 prescribe administrative procedures for maintaining the FAR System.',
        ' (4) Evaluating\tcontract proposals. (5) Awarding\tGovernment contracts. (6) Administering\tcontracts (including ordering changes or giving technical direction\tin contract performance or contract quantities, evaluating contractor\tperformance, and accepting or rejecting contractor products or services). (7) Terminating\tcontracts. (8) Determining\twhether contract costs are reasonable, allocable, and allowable. (1) Planning acquisitions. (2) Determining\twhat supplies or services are to be acquired by the Government,\tincluding developing statements of work.',
        ' (3) The Contractor\tshall- (i) Comply, and require compliance\tby the covered employee, with any conditions imposed by the Government\tas necessary to mitigate the personal conflict of interest; or (ii) Remove\tthe Contractor employee or subcontractor employee from performance\tof the contract or terminate the applicable subcontract. (d) Subcontracts. The Contractor shall include\tthe substance of this clause, including this paragraph (d), in subcontracts\u2014 (1) That exceed the simplified\tacquisition threshold, as defined in Federal Acquisition Regulation 2.101 on the date of subcontract\taward; and (2) In which\tsubcontractor employees will perform acquisition functions closely\tassociated with inherently governmental functions (i.e.,\tinstead of performance only by a self-employed individual).'
    ]
    assert context0 == context_expected[0]
    assert context1 == context_expected[1]
    assert context2 == context_expected[2]


# Remove all files generated
# datasets required for testing.
def test_delete_generated_files():
    generated_files = os.listdir(f"{data_loc}")
    for file in generated_files:
        if file == 'context.json' or file == 'sentence_context_connector.json':
            os.remove(f"{data_loc}/{file}")