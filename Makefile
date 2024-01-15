BUILDER := grpc-plugin-server-builder
IMAGE_NAME := $(shell basename "$$(pwd)")-app

SOURCE_DIR := src
VENV_DIR := venv

PROJECT_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: venv test

clean:
	cd ${SOURCE_DIR}/app/proto \
		&& rm -fv *_grpc.py *_pb2.py *_pb2.pyi *_pb2_grpc.py

proto: clean
	docker run -t --rm -u $$(id -u):$$(id -g) -v $(PROJECT_DIR):/data/ -w /data rvolosatovs/protoc:4.0.0 \
			--proto_path=app/proto=${SOURCE_DIR}/app/proto \
			--python_out=${SOURCE_DIR} \
			--grpc-python_out=${SOURCE_DIR} \
			${SOURCE_DIR}/app/proto/*.proto

venv:
	python3.9 -m venv ${VENV_DIR} \
			&& ${VENV_DIR}/bin/pip install -r requirements-dev.txt

build: proto

run: proto
	docker run --rm -it -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e HOME=/data --entrypoint /bin/sh python:3.9-slim \
			-c 'ln -sf $$(which python) ${VENV_DIR}/bin/python-docker \
					&& PYTHONPATH=${SOURCE_DIR} GRPC_VERBOSITY=debug ${VENV_DIR}/bin/python-docker -m app --enable_reflection'

help: proto
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e HOME=/data --entrypoint /bin/sh python:3.9-slim \
			-c 'ln -sf $$(which python) ${VENV_DIR}/bin/python-docker \
					&& PYTHONPATH=${SOURCE_DIR} ${VENV_DIR}/bin/python-docker -m app --help'

image: proto
	docker buildx build -t ${IMAGE_NAME} --load .

imagex: proto
	docker buildx inspect $(BUILDER) || docker buildx create --name $(BUILDER) --use 
	docker buildx build -t ${IMAGE_NAME} --platform linux/arm64/v8,linux/amd64 .
	docker buildx build -t ${IMAGE_NAME} --load .
	docker buildx rm --keep-state $(BUILDER)

imagex_push: proto
	@test -n "$(IMAGE_TAG)" || (echo "IMAGE_TAG is not set (e.g. 'v0.1.0', 'latest')"; exit 1)
	@test -n "$(REPO_URL)" || (echo "REPO_URL is not set"; exit 1)
	docker buildx inspect $(BUILDER) || docker buildx create --name $(BUILDER) --use
	docker buildx build -t ${REPO_URL}:${IMAGE_TAG} --platform linux/arm64/v8,linux/amd64 --push .
	docker buildx rm --keep-state $(BUILDER)

test: proto
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e HOME=/data --entrypoint /bin/sh python:3.9-slim \
			-c 'ln -sf $$(which python) ${VENV_DIR}/bin/python-docker \
					&& PYTHONPATH=${SOURCE_DIR} ${VENV_DIR}/bin/python-docker -m tests'

test_functional_local_hosted: proto
	@test -n "$(ENV_PATH)" || (echo "ENV_PATH is not set"; exit 1)
	docker build --tag matchmaking-test-functional -f test/functional/Dockerfile test/functional
	docker run --rm -t \
		--env-file $(ENV_PATH) \
		-e HOME=/data \
		-u $$(id -u):$$(id -g) \
		-v $$(pwd):/data \
		-w /data matchmaking-test-functional bash ./test/functional/test-local-hosted.sh

test_functional_accelbyte_hosted: proto
	@test -n "$(ENV_PATH)" || (echo "ENV_PATH is not set"; exit 1)
	docker build --tag matchmaking-test-functional -f test/functional/Dockerfile test/functional
	docker run --rm -t \
		--env-file $(ENV_PATH) \
		-e HOME=/data \
		-e PROJECT_DIR=$(PROJECT_DIR) \
		-u $$(id -u):$$(id -g) \
		--group-add $$(getent group docker | cut -d ':' -f 3) \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $$(pwd):/data \
		-w /data matchmaking-test-functional bash ./test/functional/test-accelbyte-hosted.sh

ngrok:
	@test -n "$(NGROK_AUTHTOKEN)" || (echo "NGROK_AUTHTOKEN is not set" ; exit 1)
	docker run --rm -it --net=host -e NGROK_AUTHTOKEN=$(NGROK_AUTHTOKEN) ngrok/ngrok:3-alpine \
			tcp 6565	# gRPC server port