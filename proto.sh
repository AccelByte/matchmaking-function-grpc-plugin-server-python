#!/bin/bash

set -eou pipefail

shopt -s globstar

clean_generated_files() {
  find "$1" -type f \( \
    -name '*_pb2.py' -o \
    -name '*_pb2.pyi' -o \
    -name '*_pb2_grpc.py' -o \
    -name '*_grpc.py' -o \
    -name '*.pyc' \
  \) -delete

  find "$1" -type d -name '__pycache__' -exec rm -rf {} +
}

PROTO_DIR="${1:-proto}"
OUT_DIR="${2:-src}"

# Ensure output directory exists.
mkdir -p "${OUT_DIR}"

# Clean previously generated files.
clean_generated_files "${OUT_DIR}"

# Generate protobuf files.
python -m grpc_tools.protoc \
  -I"${PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  --pyi_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTO_DIR}"/**/*.proto
