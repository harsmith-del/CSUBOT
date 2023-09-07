import urllib3
import json

container_prefix='bhopkinson'
http = urllib3.PoolManager()
app_port = 20239

index_data = json.dumps( {  'doc_name': 'doc_embedding', 
                'data_path': '/tmp/data/FAR_dita_html', 
                'ds_path': '/tmp/data', 
                'retriever': 'Embedding', 
                'docstore_type': 'elasticsearch'})

response = http.request('POST',
                        f'http://localhost:{app_port}/build_index', 
                        headers={'Content-Type': 'application/json'},
                        body=index_data)
print('done')