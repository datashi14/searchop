.PHONY: demo install data features train evaluate api test clean help kind-setup kind-load-image kind-deploy kind-teardown

help:
	@echo "SearchOp - E-Commerce AI Ranking System"
	@echo ""
	@echo "Available commands:"
	@echo "  make demo        - Run full demo: generate data, train model, start API"
	@echo "  make install     - Install dependencies"
	@echo "  make data        - Generate demo data"
	@echo "  make features    - Build feature store"
	@echo "  make train       - Train ranking model"
	@echo "  make evaluate    - Evaluate model metrics"
	@echo "  make api         - Start FastAPI service"
	@echo "  make test        - Run all tests"
	@echo "  make clean       - Clean generated files"

install:
	pip install -r requirements.txt

data:
	@echo "Generating realistic demo data..."
	PYTHONPATH=. python scripts/generate_demo_data.py

data-simple:
	@echo "Generating simple synthetic data..."
	PYTHONPATH=. python src/data_ingestion/generate_synthetic_data.py

features:
	@echo "Building feature store..."
	PYTHONPATH=. python src/data_ingestion/build_feature_store.py

train:
	@echo "Training ranking model..."
	PYTHONPATH=. python src/models/train_ranking_model.py

evaluate:
	@echo "Evaluating model..."
	PYTHONPATH=. python src/models/evaluate_model.py

api:
	@echo "Starting FastAPI service..."
	@echo "API will be available at http://localhost:8000"
	@echo "Docs at http://localhost:8000/docs"
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

demo: data features train evaluate
	@echo ""
	@echo "=========================================="
	@echo "Demo setup complete!"
	@echo "=========================================="
	@echo ""
	@echo "Model trained and evaluated."
	@echo "Metrics saved to artifacts/metrics.json"
	@echo ""
	@echo "To start the API, run:"
	@echo "  make api"
	@echo ""
	@echo "Or in a separate terminal:"
	@echo "  uvicorn src.api.main:app --reload"
	@echo ""
	@echo "Test the ranking endpoint:"
	@echo '  curl -X POST "http://localhost:8000/rank" \\'
	@echo '    -H "Content-Type: application/json" \\'
	@echo '    -d '"'"'{'
	@echo '      "query": "running shoes",'
	@echo '      "user_id": "u-1",'
	@echo '      "products": ['
	@echo '        {"id": 1, "title": "Nike Running Shoes", "price": 99.99, "category": "sports_outdoors"}'
	@echo '      ]'
	@echo '    }'"'"''
	@echo ""

test:
	@echo "Running tests..."
	PYTHONPATH=. pytest tests/ -v --tb=short

test-unit:
	PYTHONPATH=. pytest tests/unit -v

test-integration:
	PYTHONPATH=. pytest tests/integration -v -m integration

clean:
	@echo "Cleaning generated files..."
	rm -rf data/raw/*.csv
	rm -rf data/processed/*.parquet
	rm -rf data/eval/*.parquet
	rm -rf models/*.pkl
	rm -rf models/current_model_version.txt
	rm -rf artifacts/*.json
	@echo "Clean complete. Run 'make demo' to regenerate."

kind-setup:
	@echo "Setting up local Kubernetes cluster..."
	@chmod +x infra/local-cluster/setup.sh
	./infra/local-cluster/setup.sh

kind-load-image:
	@echo "Building and loading Docker image to kind..."
	docker build -f docker/Dockerfile.api -t searchop-api:latest .
	kind load docker-image searchop-api:latest --name searchop-local

kind-deploy:
	@echo "Deploying to local Kubernetes cluster..."
	kubectl apply -k k8s/overlays/local/
	@echo ""
	@echo "Waiting for deployment..."
	kubectl wait --for=condition=available deployment/searchop-api -n searchop --timeout=300s
	@echo ""
	@echo "Deployment complete!"
	@echo "Port forward: kubectl port-forward -n searchop service/searchop-api 8000:80"

kind-teardown:
	@echo "Tearing down local Kubernetes cluster..."
	@chmod +x infra/local-cluster/teardown.sh
	./infra/local-cluster/teardown.sh

