from typing import *

import MySQLdb #type: ignore
import asyncio
import argparse
    
mysql_connect = {}
db_connect = None
def get_connection():
	global db_connect
	
	if db_connect is not None:
		return db_connect

	db_connect = MySQLdb.connect(**mysql_connect)
	return db_connect

def get_mysql_dump_str(table : str) -> str:
	cmd = f'mysqldump --defaults-file=/longtmp/temp-mysql-pushcoin/mysql/my.cnf {mysql_connect["db"]}'
	
	user = mysql_connect.get( 'user' )
	if user:
		cmd += f' --user={user}'
	
	password = mysql_connect.get( 'passwd' )
	if password:
		cmd += f' --password={password}' #TODO: escaping for shell? Or not use shell
		
	socket = mysql_connect.get( 'unix_socket' )
	if socket:
		cmd += f' --socket={socket}'
		
	port = mysql_connect.get( 'port' )
	if port:
		cmd += f' --port={port}'
		
	cmd += f' --result-file=/tmp/{table}.sql {table}'
	return cmd
	
	
def list_ordered_tables() -> List[Tuple[str,int]]:
	db = get_connection()
	
	cur = db.cursor()
	cur.execute( 'select TABLE_NAME, (INDEX_LENGTH + DATA_LENGTH) as SIZE from information_schema.TABLES where TABLE_SCHEMA="sbtest"')

	tables = [(row[0],row[1]) for row in cur.fetchall()]
	sorted_tables = list(reversed(sorted(tables, key=lambda table: table[1])))
	
	return sorted_tables

async def backup_tables(names : List[str]) -> None:
	all_cmds = [get_mysql_dump_str(name) for name in names]
	
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
	global mysql_connect
	
	cli_args = argparse.ArgumentParser( description = "MySQL Ripper", allow_abbrev = False )
	
	group = cli_args.add_argument_group( "MySQL Connection" )
	group.add_argument( '--user'  )
	group.add_argument( '--passwd' )
	group.add_argument( '--db' )
	group.add_argument( '--unix-socket' )
	group.add_argument( '--port' )
	group.add_argument( '--host' )
	
	args = cli_args.parse_args()
	
	mysql_connect = {}
	if args.user:
		mysql_connect['user'] = args.user
	if args.passwd:
		mysql_connect['passwd'] = args.passwd
	if args.db:
		mysql_connect['db'] = args.db
	if args.unix_socket:
		mysql_connect['unix_socket'] = args.unix_socket
	if args.host:
		mysql_connect['host'] = args.host
	if args.port:
		mysql_connect['port'] = args.port
	
	
	sorted_tables = list_ordered_tables()
	asyncio.get_event_loop().run_until_complete( backup_tables( [table[0] for table in sorted_tables] ) )
	
main()
