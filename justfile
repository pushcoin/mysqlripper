check: 
	mypy mysqlripper/*.py
	
freeze:
	pip freeze --local > requirements.txt

build:
	python setup.py sdist bdist_wheel
