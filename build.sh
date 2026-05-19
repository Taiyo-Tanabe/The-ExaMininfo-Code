#!/bin/bash
# Render のビルドコマンドとして使用
set -e

echo "=== Python dependencies ==="
pip install -r requirements.txt

echo "=== Frontend build ==="
cd frontend
npm ci
npm run build
cd ..

echo "=== DB migration ==="
alembic upgrade head

echo "=== Build complete ==="
