PROTO_DIR = app/proto
SOURCE_DIR = src
TESTS_DIR = tests
VENV_DIR = venv
VENV_DEV_DIR = venv-dev

IMAGE_NAME := plugin-arch-grpc-server-python-app

setup:
	rm -rf ${VENV_DEV_DIR} 
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'python -m venv ${VENV_DEV_DIR} \
					&& ${VENV_DEV_DIR}/bin/pip install --upgrade pip \
					&& ${VENV_DEV_DIR}/bin/pip install -r requirements-dev.txt'

	rm -rf ${VENV_DIR}
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'python -m venv ${VENV_DIR} \
					&& ${VENV_DIR}/bin/pip install --upgrade pip \
					&& ${VENV_DIR}/bin/pip install -r requirements.txt'

clean:
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_grpc.py
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2.py
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2.pyi
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2_grpc.py

proto: clean
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data/ rvolosatovs/protoc:3.3.0 \
		--proto_path=${PROTO_DIR}=${SOURCE_DIR}/${PROTO_DIR} \
		--python_out=${SOURCE_DIR} \
		--grpc-python_out=${SOURCE_DIR} \
		${SOURCE_DIR}/${PROTO_DIR}/*.proto

build: proto

image:
	docker buildx build -t ${IMAGE_NAME} --load .

imagex:
	docker buildx inspect ${IMAGE_NAME}-builder \
			|| docker buildx create --name ${IMAGE_NAME}-builder --use 
	docker buildx build -t ${IMAGE_NAME} --platform linux/arm64/v8,linux/amd64 .
	docker buildx build -t ${IMAGE_NAME} --load .
	#docker buildx rm ${IMAGE_NAME}-builder

lint:
	rm -f lint.err
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip -e PYLINTHOME=/data/.cache/pylint  --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${TESTS_DIR}:${SOURCE_DIR}:${PROTO_DIR} ${VENV_DEV_DIR}/bin/python -m pylint -j 0 app || exit $$(( $$? & (1+2+32) ))' \
					|| touch lint.err
	[ ! -f lint.err ]

beautify:
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data/ cytopia/black:22-py3.9 \
		${SOURCE_DIR} \
		${TESTS_DIR}

test:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${TESTS_DIR}:${SOURCE_DIR}:${PROTO_DIR} ${VENV_DEV_DIR}/bin/python -m app_tests'

help:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} ${VENV_DIR}/bin/python -m app --help'

run:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} GRPC_VERBOSITY=debug ${VENV_DIR}/bin/python -m app --enable_reflection'