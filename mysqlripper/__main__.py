from typing import *
from .types import *
from . import mysql

import asyncio, argparse, logging, shlex

	
async def backup_tables(db, names : List[str], output_prefix : str, proc_count : int) -> None:
	all_cmds = [db.get_dump_cmd(name, output_prefix) for name in names]
	
	pending : Dict[asyncio.Future,Tuple[asyncio.subprocess.Process,int]] = {}
	cmd_at = 0
	while True:
		# add tasks as there is space
		while len(pending) < proc_count and cmd_at < len(all_cmds):
			logging.debug( f"adding {names[cmd_at]} task. {len(pending)+1} of {proc_count}" )
			cmd = all_cmds[cmd_at]
			cmd_str = " ".join([shlex.quote(s) for s in cmd])
			logging.debug( cmd_str )
			proc = await asyncio.create_subprocess_shell(cmd_str, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
			key = asyncio.create_task(proc.communicate())
			pending[key] = (proc, cmd_at)
			cmd_at += 1
			
		# done?
		if len(pending) == 0:
			return
			
		done_tasks : Set[asyncio.Future]
		done_tasks, _ = await asyncio.wait({k for k in pending.keys()}, return_when = asyncio.FIRST_COMPLETED )
		
		for d in done_tasks:
			assert d.done()
			result = d.result()
				
				
			proc, cmd_ndx = pending[d]
			
			logging.info( f"done:{names[cmd_ndx]}" )
			
			stdout = result[0]
			if len(stdout) > 0:
				print( names[cmd_ndx], "\n", stdout )
				
			if proc.returncode != 0:
				logging.error( d.exception() )
				raise Exception( "Failed command", cmd )

			del pending[d]

			
def backup( db, output_prefix : str, proc_count : int ) -> None:
	db.lock()
	try:
		sorted_tables = db.list_ordered_tables()
		if len(sorted_tables) == 0:
			logging.warning( "No tables found for dumping" )
			
		if logging.getLogger().isEnabledFor(logging.DEBUG):
			for table in sorted_tables:
				logging.debug( f'{table[0]} {table[1]/(1024*1024):.2f}mb' )
		task = backup_tables( db, [table[0] for table in sorted_tables], output_prefix, proc_count )
		asyncio.get_event_loop().run_until_complete( task )
	
	finally:
		db.unlock()

	
def main():
	cli_args = argparse.ArgumentParser( description = "MySQL Ripper", allow_abbrev = False )

	cli_args.add_argument( '--output-prefix', required=True )
	cli_args.add_argument( '--type', choices = [e.name for e in DBType], default='master' )
	cli_args.add_argument( '--log', default='warning' )
	cli_args.add_argument( '--proc-count', default=4, type=int )
	
	group = cli_args.add_argument_group( "MySQL Connection" )
	group.add_argument( '--user'  )
	group.add_argument( '--pass',  dest='pass_' )
	group.add_argument( '--db', required=True)
	group.add_argument( '--socket' )
	group.add_argument( '--port', type=int )
	group.add_argument( '--host' )
	
	args = cli_args.parse_args()
	
	logging.basicConfig(
		level = getattr(logging, args.log.upper(), None ),
		format = '%(asctime)s|%(levelname)s|%(message)s',
		datefmt = '%Y-%m-%dT%H:%M:%S'
	)
	
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
		
	db = mysql.MySQLRip( dargs, DBType[args.type] )

	backup(db, args.output_prefix, args.proc_count )
	
main()
