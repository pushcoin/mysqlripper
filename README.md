Parallel MySQL dumping tool.


# Operation

MySQLRipper invokes `mysqldump` to dump tables from a database. It runs multiple dumps in parallel to maximize available resources. Tables are dumped from the largest to smallest.


# Setup

For running only you can run:

```
python -m pip install -r run-requirements.txt
```

For developmen use the `requirements.txt` file.

# Invocation

```
python -m mysqlripper --help
```


## --type

The type determines how the DB will be locked during the dump:

- none: No setup/teardown will be performed.
- master: The tables will be flushed and read lock acquired. The tables are unlocked post-processing.
- slave: The slave will be stopped before processing and started once complete.

The cleanup will be performed even in the case of dump failure.
