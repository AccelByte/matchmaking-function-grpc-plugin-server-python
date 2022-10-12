PROTO_DIR = app/proto
SOURCE_DIR = src
TESTS_DIR = tests
VENV_DIR = venv
VENV_DEV_DIR = venv-dev

PYTHON_EXEC = python3.9

setup:
	rm -rf ${VENV_DEV_DIR} && \
		${PYTHON_EXEC} -m venv ${VENV_DEV_DIR} && \
		${VENV_DEV_DIR}/bin/pip install --upgrade pip && \
		${VENV_DEV_DIR}/bin/pip install -r requirements-dev.txt
	rm -rf ${VENV_DIR} && \
		${PYTHON_EXEC} -m venv ${VENV_DIR} && \
		${VENV_DIR}/bin/pip install --upgrade pip && \
		${VENV_DIR}/bin/pip install -r requirements.txt

clean:
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_grpc.py
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2.py
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2.pyi
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2_grpc.py

generate: clean
	${VENV_DEV_DIR}/bin/python -m grpc_tools.protoc \
		--proto_path=${PROTO_DIR}=${SOURCE_DIR}/${PROTO_DIR} \
		--python_out=${SOURCE_DIR} \
		--grpc_python_out=${SOURCE_DIR} \
		${SOURCE_DIR}/${PROTO_DIR}/*.proto

beautify:
	${VENV_DEV_DIR}/bin/pip install --upgrade black
	${VENV_DEV_DIR}/bin/python -m black ${SOURCE_DIR}
	${VENV_DEV_DIR}/bin/python -m black ${TESTS_DIR}

test:
	PYTHONPATH=${TESTS_DIR}:${SOURCE_DIR}:${PROTO_DIR} \
 		${VENV_DEV_DIR}/bin/python -m app_tests

help:
	PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} \
 		${VENV_DIR}/bin/python -m app --help

run:
	PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} \
		GRPC_VERBOSITY=debug \
 		${VENV_DIR}/bin/python -m app \
 		--enable_reflection