Create config file and separate datadir.

# Configure MySQL

```
mysql --defaults-file=mysql/my.cnf --user=root -p

set password = "rootpass";

create database sbtest;
```

I added the `first-table` option to call this multiple times with different table names/indexes.

```
sysbench --mysql-socket=../mysqld.sock /usr/share/sysbench/oltp_point_select.lua prepare --table-size=1000 --tables=25 --first-table=6 --mysql-user=root --mysql-password=rootpass
```
