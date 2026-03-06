.PHONY: dev test

dev:
	uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

test:
	pytest tests/ -v
