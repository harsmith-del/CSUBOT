# DOCBot
#### Transformer-based semantic search & summarization tool

## Overview

This repository allows for Q&A search of any document. The search proceeds in several stages. First, the natural language query is embedded and compared against embedded sections of the relevant document to _retrieve_ the most relevant sections. The relevant sections are _ranked_, _merged_, and then presented to a deep-neural network-based language model for _summarization_. The summary and relevant sections are presented to the user in a graphical user interface.  Our implementation makes heavy use of the Haystack framework (https://haystack.deepset.ai). 

The program consists of a steamlit front end that communicates via http with fastapi backend components for search. All components run in Docker containers. 

## Who Should Use This?

Your team should utilize the DOCBot if your project requires any of the below features:

:white_check_mark: Q&A chatbot-like features for any document without the worry of generated AI hallucinations. <br/>
:white_check_mark: Fast and powerful transformer-based semantic search. <br/>
:white_check_mark: Relevance score and retrieved document source for easy document citing. <br/>
:white_check_mark: Summarized answer of retrieved documents from large language models (LLM). <br/>

## DOCBot Technical Features

- Buildable Dockerfile setup with a production level Elasticsearch server (python base image)
- Passes SonarQube quality and security scans
- Well-written, fully documented and type-hinted python code
- Store embeded documents using FAISS, SQL, or Elasticsearch indexing
- Select between TFIDF or Embedding Transformer based document retrieval
- Utilize open source T5 summarization LLM or connect to OpenAI GPT3.5 text-davinci-003 using a OpenAI key
- Currently allows parsing of PDF, DOCX, or HTML document files
- Allow for easy customization by implementing new document extracting functions

## How To Run DOCBot

### Pre-requisites

Before running DOCBot ensure that the following pre-requisites are complete:

  - Docker must be installed and available on your machine
  - You should have a GPU-equipped compute instance for low-latency retrieval 

### Getting DOCBot Running

  1. A new user first must edit the sample.env file to match their environment. The file should then be renamed to ".env". The suggested settings should work for most use cases. 
  2. Run the command: `make getting-started` which will create required directories **/data**, **/artifacts**, **/artifacts/nltk_data**, **/logs**, **/test/logs**. 
  3. Place the desired documents in the **/data** directory.
  4. Set the *data_path* parameter value passed into the *build_index* function in the main
  function in **/src/indexer/build_indices.py**.
  5. Set the *doc_name* variable in the configs list in the main function in **/src/indexer/build_indices.py** . This will be the name of the document database index created and will be used to refer to the embedded document.
  6. Run the command: `make create-indices` which will ingest relevant documents and create a new index with the embedded documents.
  7. Confirm the **/src/util/vars.py** ES_INDEX variable matches the doc_name given
  in **/src/indexer/build_indices.py** as this will connect the appropriate document database to the QA bot.
  8. The streamlit GUI can now be activated with `make gui` and the front-end can be activated with `make up`.
  9. Open a browser and go to `http://localhost:{ST_PORT}` to view the streamlit GUI and `http://localhost:{NGINX_PORT}` to view the front-end as specified in the **.env** file.
  10. To stop the application enter the command: `make down`

## DOCBot Streamlit GUI Usage
In the streamlit GUI you may select parameters on the left hand side:
- document options: The document index to use (if there are multiple, make sure to select the appropriate index when using the bot)
- Number to Retrieve: Number of relevant sections to retrieve
- Number to Keep Post Ranking: Number of relevant sections to return after sorting by most relevant
- Retriever: Type of retriever to use (Embedding, TFIDF, DensePassage)
- Enricher: Option to add additional context to each retrieved relevant section
- Summarizer: Switch between the local T5 open source model or the OpenAI GPT3.5 text-davinci-003 model
  *NOTE: a OpenAI key must be supplied in the .env file if using the OpenAI model*
- QA Search: Toggle the QA search option instead of the summarization pipeline
- Upload Document to Search: Option to upload documents and build document database directly from streamlit GUI

Changes to these parameters will affect results in both streamlit GUI and front-end.
The streamlit GUI is meant for developer usage only.

## DOCBot Leveraged Technologies

- Python            (Modern scripting language)
- Haystack          (NLP framework for pipeline development)
- Huggingface       (NLP transformers library to utilize state of the art LLM models)
- Streamlit         (Web app development framework)
- Elasticsearch     (Industry leading search index)
- FastAPI           (REST API framework)
- Gunicorn          (Production level WSGI server)
- Docker            (Containerization platform)
