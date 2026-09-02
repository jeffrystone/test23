# Unix/macOS (needs `make`). On Windows use setup.bat / run.bat instead.
# Runtime deps work on Python 3.10+. Full lockfile: src/requriments.txt (Python >=3.11).

venv:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r ./requirements-runtime.txt

run:
	mkdir -p ./staticfiles/logs
	PYTHONPATH=. ./venv/bin/python src/main.py
