PROTO_DIR = src/app/proto
SOURCE_DIR = src
VENV_DIR = venv

PYTHON_EXEC = python3.9

setup:
	rm -rf ${VENV_DIR}
	${PYTHON_EXEC} -m venv ${VENV_DIR}
	${VENV_DIR}/bin/pip install --upgrade pip
	${VENV_DIR}/bin/pip install -r requirements.txt

clean:
	rm -f ${PROTO_DIR}/*_grpc.py
	rm -f ${PROTO_DIR}/*_pb2.py
	rm -f ${PROTO_DIR}/*_pb2.pyi
	rm -f ${PROTO_DIR}/*_pb2_grpc.py

generate: clean
	${VENV_DIR}/bin/python -m grpc_tools.protoc \
		-I${PROTO_DIR} \
		--python_out=${PROTO_DIR} \
		--grpc_python_out=${PROTO_DIR} \
		${PROTO_DIR}/*.proto

run:
	PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} \
 		${VENV_DIR}/bin/python -m app
