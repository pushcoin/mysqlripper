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

To stop mysql

```
mysqladmin --defaults-file=my.cnf -p shutdown --user=root
```

To connect with localhost use `--host=127.0.0.1` instead, otherwise mysql will attempt to use a socket connection.

## Sample my.cnf

```
[mysql]

[client]
port = 3337
socket = /longtmp/temp-mysql-pushcoin/mysqld.sock

[mysqld]
user = mysql
pid-file = /longtmp/temp-mysql-pushcoin/mysqld.pid
socket = /longtmp/temp-mysql-pushcoin/mysqld.sock
port = 3337
basedir = /usr
datadir = /longtmp/temp-mysql-pushcoin/data
log_bin = mysql-bin
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
skip-external-locking
bind-address = 127.0.0.1
server-id = 1
```

## Slave setup function to test

### Sample slave.cnf

```
[mysql]

[client]
port = 3338
socket = /longtmp/temp-mysql-pushcoin/slave/mysqld.sock

[mysqld]
user = mysql
pid-file = /longtmp/temp-mysql-pushcoin/slave/mysqld.pid
socket = /longtmp/temp-mysql-pushcoin/slave/mysqld.sock
port = 3338
basedir = /usr
datadir = /longtmp/temp-mysql-pushcoin/slave/data
log_bin = mysql-bin
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
skip-external-locking
bind-address = 127.0.0.1
server-id = 2
```

On master:
```
GRANT REPLICATION SLAVE ON *.* TO 'slave_user'@'%' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;

SHOW MASTER STATUS;
```

Dump master:
```
mysqldump --all-databases --user=root --password --port=3337 --host=127.0.0.1 --master-data > /tmp/everything.sql
```

Create slave:
```
mkdir /longtmp/temp-mysql-pushcoin/slave
mysqld --initialize --user=mysql --datadir=/longtmp/temp-mysql-pushcoin/slave/data
mysql --defaults-file=slave.cnf --user=root -p
set password = "rootpass";
STOP SLAVE;

CHANGE MASTER TO MASTER_HOST='127.0.0.1',MASTER_USER='slave_user', MASTER_PASSWORD='password', MASTER_LOG_FILE='mysql-bin.000001', MASTER_LOG_POS=154;
```

Import data:
```
mysql --user=root -p  --port=3338 --host=127.0.0.1 < /tmp/everything.sql
```

```
DELIMITER $$
CREATE PROCEDURE mysql.rds_stop_replication()
BEGIN
	STOP SLAVE;
	SELECT 'Slave has been stopped';
END $$
DELIMITER ;
```


## Sample Run

```
python -m mysqlripper --db sbtest --host 127.0.0.1 --user root --pass rootpass --output-prefix /tmp/dump --port 3337
```
