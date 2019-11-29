from typing import *

import MySQLdb #type: ignore
import asyncio
import argparse
    
mysql_connect : Dict[str,str] = {}
db_connect = None
def get_connection():
	global db_connect
	
	if db_connect is not None:
		return db_connect

	cnx = mysql_connect.copy()
	if 'pass' in cnx:
		cnx['passwd'] = cnx.pop('pass')
	if 'socket' in cnx:
		cnx['unix_socket'] = cnx.pop('socket')
	
	print(cnx)
	db_connect = MySQLdb.connect(**cnx)
	return db_connect

def get_mysql_dump_cmd(table : str, output_prefix : str) -> List[str]:
	cmd = ['mysqldump', mysql_connect["db"]]
	#'--defaults-file=/longtmp/temp-mysql-pushcoin/mysql/my.cnf',
	
	user = mysql_connect.get( 'user' )
	if user:
		cmd.append( f'--user={user}' )
	
	password = mysql_connect.get( 'pass' )
	if password:
		cmd.append( f'--password={password}')
		
	socket = mysql_connect.get( 'socket' )
	if socket:
		cmd.append( f'--socket={socket}' )
		
	port = mysql_connect.get( 'port' )
	if port:
		cmd.append( f'--port={port}' )
		
	cmd.append( f'--result-file={output_prefix}{table}.sql' )
	cmd.append( table )
	return cmd
	
	
def list_ordered_tables() -> List[Tuple[str,int]]:
	db = get_connection()
	
	cur = db.cursor()
	cur.execute( 'select TABLE_NAME, (INDEX_LENGTH + DATA_LENGTH) as SIZE from information_schema.TABLES where TABLE_SCHEMA="sbtest"')

	tables = [(row[0],row[1]) for row in cur.fetchall()]
	sorted_tables = list(reversed(sorted(tables, key=lambda table: table[1])))
	
	return sorted_tables

	
async def backup_tables(names : List[str], output_prefix : str) -> None:
	all_cmds = [get_mysql_dump_cmd(name, output_prefix) for name in names]
	
	pending : Dict[asyncio.Future,Tuple[asyncio.subprocess.Process,List[str]]] = {}
	proc_count = 4
	cmd_at = 0
	while True:
		# add tasks as there is space
		while len(pending) < proc_count and cmd_at < len(all_cmds):
			cmd = all_cmds[cmd_at]
			proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
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

	cli_args.add_argument( '--output-prefix', required=True )
	
	group = cli_args.add_argument_group( "MySQL Connection" )
	group.add_argument( '--user'  )
	group.add_argument( '--pass',  dest='pass_' )
	group.add_argument( '--db', required=True)
	group.add_argument( '--socket' )
	group.add_argument( '--port' )
	group.add_argument( '--host' )
	
	args = cli_args.parse_args()
	
	mysql_connect = {}
	if args.user:
		mysql_connect['user'] = args.user
	if args.pass_:
		mysql_connect['pass'] = args.pass_
	if args.db:
		mysql_connect['db'] = args.db
	if args.socket:
		mysql_connect['socket'] = args.socket
	if args.host:
		mysql_connect['host'] = args.host
	if args.port:
		mysql_connect['port'] = args.port
	
	
	sorted_tables = list_ordered_tables()
	task = backup_tables( [table[0] for table in sorted_tables], args.output_prefix )
	asyncio.get_event_loop().run_until_complete( task )
	
main()
