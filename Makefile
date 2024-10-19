run:
	python main.py

install:
	pip install -r requirements.txt


build:
	python setup.py build bdist_wheel

clean:
	rm -Rf build dist langcode.egg-info

.PHONY: test
test:
	PYTHONPATH=. pytest