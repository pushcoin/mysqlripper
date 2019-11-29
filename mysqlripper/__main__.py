from typing import *

import MySQLdb #type: ignore
import asyncio
    
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

async def backup_tables(names : List[str]):
	all_cmds = [
		f'mysqldump --defaults-file=/longtmp/temp-mysql-pushcoin/mysql/my.cnf sbtest --user=root --password="rootpass" --result-file=/tmp/{name}.sql {name}' for name in names
	]
	
	pending : Dict[asyncio.Future,Tuple[asyncio.subprocess.Process,str]] = {}
	proc_count = 4
	cmd_at = 0
	while True:
		# add tasks as there is space
		while len(pending) < proc_count and cmd_at < len(all_cmds):
			cmd = all_cmds[cmd_at]
			proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
			key = asyncio.create_task(proc.communicate())
			pending[key] = (proc, cmd)
			cmd_at += 1
			
		# done?
		if len(pending) == 0:
			return
			
		done_tasks : Set[asyncio.Future]
		done_tasks, _ = await asyncio.wait({k for k in pending.keys()}, return_when = asyncio.FIRST_COMPLETED )
		
		for d in done_tasks:
			assert d.done()
			result = d.result()
				
			proc, cmd = pending[d]
			#print(cmd)
			if proc.returncode != 0:
				print( d.exception() )
				raise Exception( "Failed command", cmd )

			del pending[d]
			
		
	
def main():
	sorted_tables = list_ordered_tables()
	asyncio.get_event_loop().run_until_complete( backup_tables( [table[0] for table in sorted_tables] ) )
	
main()
