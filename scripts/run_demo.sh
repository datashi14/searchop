#!/bin/bash
# Run full demo: generate data, train model, evaluate

set -e

echo "=========================================="
echo "SearchOp Demo - E-Commerce Ranking System"
echo "=========================================="
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Generate data
echo "Step 1/4: Generating demo data..."
PYTHONPATH=. python scripts/generate_demo_data.py

# Build features
echo ""
echo "Step 2/4: Building feature store..."
PYTHONPATH=. python src/data_ingestion/build_feature_store.py

# Train model
echo ""
echo "Step 3/4: Training ranking model..."
PYTHONPATH=. python src/models/train_ranking_model.py

# Evaluate
echo ""
echo "Step 4/4: Evaluating model..."
PYTHONPATH=. python src/models/evaluate_model.py

echo ""
echo "=========================================="
echo "Demo complete!"
echo "=========================================="
echo ""
echo "To start the API:"
echo "  uvicorn src.api.main:app --reload"
echo ""
echo "Or use: make api"
echo ""


