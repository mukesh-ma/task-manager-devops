.PHONY: install dev test lint fmt docker-up docker-down migrate clean

install:
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check app tests
	bandit -r app -ll

fmt:
	ruff format app tests

docker-up:
	docker compose up --build -d
	@echo "API:        http://localhost:8000/docs"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3000 (admin/admin)"

docker-down:
	docker compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml
