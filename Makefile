.PHONY: install data forecast dashboard test lint clean all

install:
	pip install -r requirements.txt

data:
	python scripts/generate_sample_data.py

forecast:
	python scripts/run_forecast_pipeline.py

dashboard:
	python scripts/build_dashboard.py

test:
	pytest tests/ -v

lint:
	ruff check src/ scripts/ tests/

all: install data forecast dashboard test

clean:
	rm -rf data/processed/*.parquet data/processed/*.csv data/processed/*.duckdb
	rm -rf reports/figures/*.png reports/*.csv reports/*.md
	rm -rf dashboard/dist/*.json dashboard/dist/index.html
	find . -name "__pycache__" -type d -exec rm -rf {} +
