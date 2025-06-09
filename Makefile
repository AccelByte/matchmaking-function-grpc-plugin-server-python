# Copyright (c) 2022 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

SHELL := /bin/bash

IMAGE_NAME := $(shell basename "$$(pwd)")-app
BUILDER := extend-builder

PYTHON_VERSION := 3.10

SOURCE_DIR := src

clean:
	cd ${SOURCE_DIR}/app/proto \
		&& rm -fv *_grpc.py *_pb2.py *_pb2.pyi *_pb2_grpc.py

proto: clean
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data rvolosatovs/protoc:4.0.0 \
			--proto_path=app/proto=${SOURCE_DIR}/app/proto \
			--python_out=${SOURCE_DIR} \
			--grpc-python_out=${SOURCE_DIR} \
			${SOURCE_DIR}/app/proto/*.proto

build: proto

run:
	docker run --rm -it -u $$(id -u):$$(id -g) \
		-e HOME=/data \
		--env-file .env \
		-v $$(pwd):/data \
		-w /data \
		--entrypoint /bin/sh \
		python:${PYTHON_VERSION}-slim \
		-c 'python -m pip install -r requirements.txt \
			&& PYTHONPATH=${SOURCE_DIR} GRPC_VERBOSITY=debug python -m app --enable_reflection'

help:
	docker run --rm -it -u $$(id -u):$$(id -g) \
		-e HOME=/data \
		--env-file .env \
		-v $$(pwd):/data \
		-w /data \
		--entrypoint /bin/sh \
		python:${PYTHON_VERSION}-slim \
		-c 'python -m pip install -r requirements.txt \
			&& PYTHONPATH=${SOURCE_DIR} python -m app --help'

image:
	docker buildx build -t ${IMAGE_NAME} --load .

imagex:
	docker buildx inspect $(BUILDER) || docker buildx create --name $(BUILDER) --use 
	docker buildx build -t ${IMAGE_NAME} --platform linux/amd64 .
	docker buildx build -t ${IMAGE_NAME} --load .
	docker buildx rm --keep-state $(BUILDER)

imagex_push:
	@test -n "$(IMAGE_TAG)" || (echo "IMAGE_TAG is not set (e.g. 'v0.1.0', 'latest')"; exit 1)
	@test -n "$(REPO_URL)" || (echo "REPO_URL is not set"; exit 1)
	docker buildx inspect $(BUILDER) || docker buildx create --name $(BUILDER) --use
	docker buildx build -t ${REPO_URL}:${IMAGE_TAG} --platform linux/amd64 --push .
	docker buildx rm --keep-state $(BUILDER)

ngrok:
	@which ngrok || (echo "ngrok is not installed" ; exit 1)
	@test -n "$(NGROK_AUTHTOKEN)" || (echo "NGROK_AUTHTOKEN is not set" ; exit 1)
	ngrok tcp 6565	# gRPC server port
