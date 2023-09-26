import os
import io
import requests
from typing import List, Dict, Tuple

import streamlit as st

#initialize session state variables the first time through
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
    st.session_state.enricher = None
    st.session_state.summarizer = None
    st.session_state.document = None

container_prefix = os.environ['CONTAINER_PREFIX']

def rebuild_summarizer(summarizer: str, 
                       retriever: str, 
                       enricher: str,
                       document: str) -> None:
    """rebuild summarizer pipeline in application
    
    parameters:
        retriever: str indicating type of semantic search retriever to use (Embedding, TfIdf, etc)
        enricher: str indicating document enricher type (none, next_doucment)
        document: str indicating document database to search
    """
    data = {'summarizer': summarizer, 
            'retriever': retriever,
            'enricher': enricher,
            'document': document}
    response = requests.post(f'http://{container_prefix}_docapp:5000/build_pipeline/summarization', json=data)

def send_query(query: str, 
               n_retrieve: int =10, 
               n_rank: int =5) -> Tuple[str, List[Dict]]:
    """send text query to summarization pipeline
    
    parameters:
        query: str, text seach query
        n_retrieve: int, number of documents to retrieve
        n_rank: int, number or documents to retain after ranking step in pipeline
    return: 
        summary: str, summary of the retrieved documents in response to query
        docs: list of relevant documents retrieved 
    """
    data = {'query': query, 
            'n_retrieve': n_retrieve,
            'n_rank': n_rank}
    response = requests.post(f'http://{container_prefix}_docapp:5000/search/summarization', json=data)
    data = response.json()
    summary = data['summary']
    docs = data['relevant_docs']
    return summary, docs

@st.cache(allow_output_mutation=True)
def send_qa_query(query: str,
                  n_retrieve: int =10, 
                  n_rank: int =5) -> Dict:
    """ send text query to question and answer pipeline

    parameters:
        query: str, text seach query
        n_retrieve: int, number of documents to retrieve
        n_rank: int, number or documents to retain after ranking step in pipeline
    return: 
        result: dictionary of answers and relevant documents output by QA pipeline
    """
    data = {'query': query, 
            'n_retrieve': n_retrieve,
            'n_rank': n_rank}
    response = requests.post(f'http://{container_prefix}_docapp:5000/search/qa', json=data)
    data = response.json()
    result = data['result']
    return result

def send_document(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    data = {'document':'new_doc',
            'filename':uploaded_file.name}
    files = {'file': io.BytesIO(bytes_data)}
    res = requests.post(f'http://{container_prefix}_docapp:5000/upload',
                         data = data,
                         files=files)
    
def build_index():
    """will build new_doc index on uploaded documents """
    data = {
        'doc_name' :'new_doc', 
        'data_path' : '/tmp/data/uploads/new_doc', 
        'ds_path' : '/tmp/data', 
        'retriever' : 'Embedding', 
        'docstore_type' :'elasticsearch',
    }
    res = requests.post(f'http://{container_prefix}_docapp:5000/build_index',
                        json = data)
    result= res.json()
    st.write(result)
    
def list_documents():
    response = requests.get(f'http://{container_prefix}_docapp:5000/documents')
    data = response.json()
    documents = [k for k in data.keys() if not k.startswith(".") and not k == "label"]  #internal indices begin with period
    return documents

st.header('Document Bot')
st.image('/usr/src/gui/Docbot_v1.png', width=200)

document_options = list_documents()
document = st.sidebar.selectbox('document options', document_options)

n_retrieve = st.sidebar.number_input('Number to Retrieve:', 
                                    min_value=1, max_value=30,
                                    value=10,step=1)
n_rank = st.sidebar.number_input('Number to Keep Post Ranking:', 
                                    min_value=1, max_value=15,
                                    value=5,step=1)
retriever = st.sidebar.selectbox('Retriever',('Embedding','TfIdf', 'DensePassage' ))
enricher = st.sidebar.selectbox('Enricher',('None','next_document'))
summarizer = st.sidebar.selectbox('Summarizer',('local','openai'))
qa_search = st.sidebar.checkbox('QA Search',value=False )
# st.sidebar.button('Build Index', on_click=build_index)

uploaded_file = st.sidebar.file_uploader("Upload Document To Search")
activate_build = st.sidebar.button("Build Index")
if activate_build:
    build_index()


if retriever != st.session_state.retriever or\
    enricher != st.session_state.enricher or\
    summarizer !=st.session_state.summarizer or\
    document != st.session_state.document:

    st.session_state.retriever = retriever
    st.session_state.enricher = enricher
    st.session_state.summarizer = summarizer
    st.session_state.document = document
    rebuild_summarizer(st.session_state.summarizer, 
                       st.session_state.retriever, 
                       st.session_state.enricher,
                       st.session_state.document)

text_query = st.text_input("Enter Query")

if uploaded_file is not None:
    send_document(uploaded_file)

if text_query != '':
    if qa_search:
        result = send_qa_query(text_query, n_retrieve, n_rank)
        st.write(result)
    else:
        summary, docs = send_query(text_query, n_retrieve, n_rank)
        #display response summary
        st.write('\n')
        st.write('__Response Summary:__')
        st.write(f'{summary}')
        st.write('\n')
        st.write('\n')
        st.write('__Relevant Sections:__')

        #display relevant documents
        for doc in docs:
            doc_path = doc['meta']['file']
            content = doc['meta']['extended_content']

            score = doc['score'] 
            if score is None:
                display_str = f'[N/A]: {content}'
            else:
                display_str = f'[{score:.2f}]: {content}'
            
            st.write(display_str)