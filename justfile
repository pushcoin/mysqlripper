#https://github.com/casey/just

check: 
	mypy mysqlripper/*.py
	
freeze:
	pip freeze --local > requirements.txt

build:
	python setup.py sdist bdist_wheel

create-venv:
	python3.7 -m venv --without-pip env 
	bash -c "source env/bin/activate; curl https://bootstrap.pypa.io/get-pip.py | python;"

	bash -c "source env/bin/activate;	pip install --upgrade pip; pip install -r requirements.txt"
	
