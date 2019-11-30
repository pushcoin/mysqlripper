from typing import *
from .types import *
from . import mysql

import asyncio
import argparse
	
async def backup_tables(db, names : List[str], output_prefix : str) -> None:
	all_cmds = [db.get_dump_cmd(name, output_prefix) for name in names]
	
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
			
def backup( db, output_prefix : str, db_type : DBType ) -> None:
	cur = db.get_cursor()
	if db_type == DBType.master:
		cur.execute( 'FLUSH TABLES WITH READ LOCK' )
	else:
		cur.execute( 'STOP SLAVE' )
		
	try:
		sorted_tables = db.list_ordered_tables()
		task = backup_tables( db, [table[0] for table in sorted_tables], output_prefix )
		asyncio.get_event_loop().run_until_complete( task )
	
	finally:
		if db_type == DBType.master:
			cur.execute('UNLOCK TABLES' )
		else:
			cur.execute('START SLAVE' )

	
def main():
	cli_args = argparse.ArgumentParser( description = "MySQL Ripper", allow_abbrev = False )

	cli_args.add_argument( '--output-prefix', required=True )
	cli_args.add_argument( '--type', choices = ['master','slave'], default='master' )
	
	group = cli_args.add_argument_group( "MySQL Connection" )
	group.add_argument( '--user'  )
	group.add_argument( '--pass',  dest='pass_' )
	group.add_argument( '--db', required=True)
	group.add_argument( '--socket' )
	group.add_argument( '--port' )
	group.add_argument( '--host' )
	
	args = cli_args.parse_args()
	
	dargs = DBConnect()
	dargs.db = args.db
	
	if args.user:
		dargs.user = args.user
	if args.pass_:
		dargs.password = args.pass_
	if args.socket:
		dargs.socket = args.socket
	if args.host:
		dargs.host = args.host
	if args.port:
		dargs.port = int(args.port)
		
	db = mysql.MySQLRip( dargs )

	backup(db, args.output_prefix, DBType[args.type] )
	
main()
