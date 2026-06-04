.PHONY: setup run test compile

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements-dev.txt

run:
	. .venv/bin/activate && PYTHONPATH=src uvicorn sellersflare.app:create_app --factory --host 127.0.0.1 --port 8088

test:
	. .venv/bin/activate && pytest -q

compile:
	. .venv/bin/activate && python -m compileall -q src tests
