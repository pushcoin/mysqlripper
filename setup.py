# https://packaging.python.org/tutorials/packaging-projects/
import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="mysqlripper",
	version="0.0.1",
	author="Edaqa Mortoray",
	author_email="edaqa@disemia.com",
	description="A parallel MySQL database dumping utility",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://bitbucket.org/pushcoin/mysqlripper",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.7',
	install_requires=[
		'mysql==0.0.2',
		'mysqlclient==1.4.6',
		'typed-ast>=1.4.0',
		'typing-extensions>=3.7.4.1',
	],
)
