import MySQLdb
import asyncio, sys

# Python 3.6 support
if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
	loop = asyncio.get_event_loop()
    
db_connect = None
def get_connection():
	global db_connect
	
	if db_connect is not None:
		return db_connect
		
	db_connect = MySQLdb.connect(user="root", passwd="rootpass", db="sbtest",
		unix_socket='/longtmp/temp-mysql-pushcoin/mysqld.sock')
	return db_connect
	
	
def list_ordered_tables():
	db = get_connection()
	
	cur = db.cursor()
	cur.execute( 'select TABLE_NAME, (INDEX_LENGTH + DATA_LENGTH) as SIZE from information_schema.TABLES where TABLE_SCHEMA="sbtest"')

	tables = [(row[0],row[1]) for row in cur.fetchall()]
	sorted_tables = list(reversed(sorted(tables, key=lambda table: table[1])))
	
	return sorted_tables

async def backup_table(name : str):
	cmd = f'mysqldump --defaults-file=/longtmp/temp-mysql-pushcoin/mysql/my.cnf sbtest --user=root --password="rootpass" --result-file=/tmp/{name}.sql {name}'
	proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	
	stdout, stderr = await proc.communicate()
	print(f'[{cmd!r} exited with {proc.returncode}]')
	
def main():
	sorted_tables = list_ordered_tables()
	for table in sorted_tables:
		loop.run_until_complete(backup_table(table[0]))
	
main()
