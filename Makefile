include .env
export

.PHONY: gui, test

down:
	docker compose -f ./docker/docker-compose.yaml \
		-f ./docker/$(DOCUMENT_STORE).yaml \
		--env-file .env down

up:
	docker compose -f ./docker/docker-compose.yaml \
		-f ./docker/$(DOCUMENT_STORE).yaml \
			--env-file .env up -d

gui:
	docker compose -f ./docker/docker-compose.yaml \
		-f ./docker/$(DOCUMENT_STORE).yaml \
			--env-file .env up -d
	@docker container exec $(COMPOSE_PROJECT_NAME)_st_docgui \
		/bin/bash -c "streamlit run doc_gui.py \
		--browser.gatherUsageStats False --server.port=8501 --server.address=0.0.0.0 2>&1" | 2>&1
	@echo "streamlit running on http://localhost:$(ST_PORT)"

_create-indices:
	@sleep 20
	@docker container exec $(COMPOSE_PROJECT_NAME)_docapp \
		/bin/bash -c "python3 ./indexer/build_indices.py"

create-indices: up _create-indices down

re-build:
	docker compose -f ./docker/docker-compose.yaml \
	-f ./docker/$(DOCUMENT_STORE).yaml \
	--env-file .env build $(SERVICE)

re-build-all:
	docker compose -f ./docker/docker-compose.yaml \
	-f ./docker/$(DOCUMENT_STORE).yaml \
		--env-file .env build

getting-started:
	mkdir -p data
	mkdir -p artifacts
	mkdir -p artifacts/nltk_data
	mkdir -p logs
	mkdir -p test/logs

test:
	docker compose -f ./test/docker-compose.yaml \
		--env-file .env up -d
	@sleep 5
	@docker container exec $(COMPOSE_PROJECT_NAME)_test_docapp \
		/bin/bash -c "python3 -m pytest /usr/src/test/code/extractor;\
						python3 -m pytest /usr/src/test/code/indexer;\
						python3 -m pytest /usr/src/test/code/pipelines;\
						python3 -m pytest /usr/src/test/code/nodes;\
						python3 -m pytest /usr/src/test/code/util;\
					"
	docker compose -f ./test/docker-compose.yaml \
		--env-file .env down