#!/bin/sh

# Exits immediately if a command exits with a non-zero status
set -e

echo "Deleting Azure resources..."
terraform -chdir=infra destroy -parallelism=10