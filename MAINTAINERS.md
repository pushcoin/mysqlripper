Create config file and separate datadir.

# Create Python 3.7 environment

```
python3.7 -m venv env
```

If that fails:

```
python3.7 -m venv --without-pip env 
source env/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
deactivate

source env/bin/activate
pip install --upgrade pip
```

# Configure MySQL

```
mysqld --initialize --user=mysql --datadir=/longtmp/temp-mysql-pushcoin/data
```

```
mysql --defaults-file=my.cnf --user=root -p

set password = "rootpass";

create database sbtest;
```

I added the `first-table` option to call this multiple times with different table names/indexes.

```
sysbench --mysql-socket=../mysqld.sock /usr/share/sysbench/oltp_point_select.lua prepare --table-size=1000 --tables=25 --first-table=6 --mysql-user=root --mysql-password=rootpass
```

To run mysql

```
mysqld --defaults-file=my.cnf
```

To connect with localhost use `--host=127.0.0.1` instead, otherwise mysql will attempt to use a socket connection.

## Sample my.cnf

```
[mysql]

[client]
port        = 3337
socket      = /longtmp/temp-mysql-pushcoin/mysqld.sock

[mysqld]
user        = mysql
pid-file    = /longtmp/temp-mysql-pushcoin/mysqld.pid
socket      = /longtmp/temp-mysql-pushcoin/mysqld.sock
port        = 3337
basedir     = /usr
datadir     = /longtmp/temp-mysql-pushcoin/data
tmpdir      = /tmp
lc-messages-dir = /usr/share/mysql
skip-external-locking
bind-address        = 127.0.0.1
#log_error = /longtmp/temp-mysql-pushcoin/error.log
#expire_logs_days    = 10
#max_binlog_size         = 100M
```
