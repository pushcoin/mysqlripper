check: 
	mypy mysqlripper/*.py
	
freeze:
	pip freeze --local > requirements.txt

