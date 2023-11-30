PROTO_DIR = app/proto
SOURCE_DIR = src
TESTS_DIR = tests
VENV_DIR = venv
VENV_DEV_DIR = venv-dev
VENV_DOCKER_DIR = venv-docker
VENV_DEV_DOCKER_DIR = venv-dev-docker

BUILDER := grpc-plugin-server-builder
IMAGE_NAME := $(shell basename "$$(pwd)")-app

.PHONY: test

clean:
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_grpc.py \
			${SOURCE_DIR}/${PROTO_DIR}/*_pb2.py \
			${SOURCE_DIR}/${PROTO_DIR}/*_pb2.pyi \
			${SOURCE_DIR}/${PROTO_DIR}/*_pb2_grpc.py

proto: clean
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data/ rvolosatovs/protoc:4.0.0 \
			--proto_path=${PROTO_DIR}=${SOURCE_DIR}/${PROTO_DIR} \
			--python_out=${SOURCE_DIR} \
			--grpc-python_out=${SOURCE_DIR} \
			${SOURCE_DIR}/${PROTO_DIR}/*.proto

setup:
	python3.9 -m venv ${VENV_DIR} \
			&& ${VENV_DIR}/bin/pip install --upgrade pip \
			&& ${VENV_DIR}/bin/pip install -r requirements.txt
	python3.9 -m venv ${VENV_DEV_DIR} \
			&& ${VENV_DEV_DIR}/bin/pip install --upgrade pip \
			&& ${VENV_DEV_DIR}/bin/pip install -r requirements-dev.txt

setup_docker:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'python3.9 -m venv ${VENV_DOCKER_DIR} \
					&& ${VENV_DOCKER_DIR}/bin/pip install --upgrade pip \
					&& ${VENV_DOCKER_DIR}/bin/pip install -r requirements.txt'
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'python3.9 -m venv ${VENV_DEV_DOCKER_DIR} \
					&& ${VENV_DEV_DOCKER_DIR}/bin/pip install --upgrade pip \
					&& ${VENV_DEV_DOCKER_DIR}/bin/pip install -r requirements-dev.txt'

build: proto

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

lint: setup_docker proto
	rm -f lint.err
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip -e PYLINTHOME=/data/.cache/pylint --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${SOURCE_DIR}/${TESTS_DIR} ${VENV_DEV_DOCKER_DIR}/bin/python -m pylint -j 0 app || exit $$(( $$? & (1+2+32) ))' \
		|| touch lint.err
	[ ! -f lint.err ]

beautify:
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data/ cytopia/black:22-py3.9 \
		${SOURCE_DIR} \
		${TESTS_DIR}

test: setup_docker proto
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${SOURCE_DIR}/${TESTS_DIR} ${VENV_DEV_DOCKER_DIR}/bin/python -m app_tests'

help: setup_docker proto
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${SOURCE_DIR}/${TESTS_DIR} ${VENV_DOCKER_DIR}r/bin/python -m app --help'

run: setup_docker proto
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${SOURCE_DIR}/${TESTS_DIR} GRPC_VERBOSITY=debug ${VENV_DOCKER_DIR}/bin/python -m app --enable_reflection'
