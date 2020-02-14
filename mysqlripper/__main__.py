from typing import *
from .types import *
from . import mysql

import asyncio, argparse, getpass, logging, os, shlex, pprint

	
async def backup_tables(db, names : List[DBObject], output_prefix : str, proc_count : int, pipe_to : str) -> None:
	all_cmds = [db.get_dump_cmd(name, output_prefix) for name in names]
	
	pending : Dict[asyncio.Future,Tuple[asyncio.subprocess.Process,int]] = {}
	cmd_at = 0
	while True:
		# add tasks as there is space
		while len(pending) < proc_count and cmd_at < len(all_cmds):
			dbobj = names[cmd_at]
			logging.debug( f"adding {names[cmd_at]} task. {len(pending)+1} of {proc_count}" )
			cmd = all_cmds[cmd_at]
			
			if pipe_to:	
				if dbobj.type_ == DBObjectType.schema:
					cmd_str = f'OBJECT_NAME=schema; '
				elif dbobj.type_ == DBObjectType.table:
					assert dbobj.name is not None
					cmd_str = f'OBJECT_NAME={shlex.quote("table_" + dbobj.name)}; '
				else:	
					raise Exception("Invalid DBObjectType", dbobj.type_ )
			else:
				cmd_str = ''
				
			cmd_str += " ".join([shlex.quote(s) for s in cmd])
			if pipe_to:
				cmd_str += f'| {pipe_to}'
			
			logging.debug( cmd_str )
			logging.info( f"start:{dbobj.type_.name} {dbobj.name}" )
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
			dbobj = names[cmd_ndx]
			logging.info( f"done:{dbobj.type_.name} {dbobj.name}" )
			
			stdout = result[0]
			if len(stdout) > 0:
				logging.info( f'{names[cmd_ndx]}:{stdout}' )
				
			if proc.returncode != 0:
				logging.error( d.exception() )
				raise Exception( "Failed command", cmd )

			del pending[d]

			
def backup( db, output_prefix : str, proc_count : int, pipe_to : str ) -> None:
	db.lock()
	try:
		sorted_tables = db.list_ordered_tables()
		if len(sorted_tables) == 0:
			logging.warning( "No tables found for dumping" )
			
		if logging.getLogger().isEnabledFor(logging.DEBUG):
			for table in sorted_tables:
				logging.debug( f'{table[0]} {table[1]/(1024*1024):.2f}mb' )
				
		objects = [DBObject(DBObjectType.table,table[0]) for table in sorted_tables]
		objects.append( DBObject(DBObjectType.schema, None) )
		task = backup_tables( db, objects, output_prefix, proc_count, pipe_to )
		asyncio.get_event_loop().run_until_complete( task )

		status = db.get_master_slave_status()
		with open( output_prefix + 'status.txt', 'w', encoding='utf-8' ) as f:
			f.write(pprint.pformat(status))
			
	finally:
		db.unlock()

password_prompt : Any = {}
type_default_none : Any = {}
	
def main() -> None:
	cli_args = argparse.ArgumentParser( description = "MySQL Ripper", allow_abbrev = False )

	cli_args.add_argument( '--type', choices = [e.name for e in DBType], default= type_default_none )
	cli_args.add_argument( '--log', default='warning' )
	cli_args.add_argument( '--proc-count', default=4, type=int )
	
	dest_group = cli_args.add_mutually_exclusive_group(required=True)
	dest_group.add_argument( '--pipe-to', type=str )
	dest_group.add_argument( '--output-prefix' )
	dest_group.add_argument( '--dump-dir' )
	
	group = cli_args.add_argument_group( "MySQL Connection" )
	group.add_argument( '--user'  )
	group.add_argument( '--pass', const = password_prompt, dest='pass_', nargs='?', default = None )
	group.add_argument( '--db', required=True)
	group.add_argument( '--socket' )
	group.add_argument( '--port', type=int )
	group.add_argument( '--host' )
	
	compress_args = cli_args.add_mutually_exclusive_group()
	compress_args.add_argument( '--gzip', action='store_true' )
	compress_args.add_argument( '--lzop', action='store_true' )
	
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
	
	if args.pass_ == password_prompt:
		dargs.password = getpass.getpass()
	elif args.pass_:
		dargs.password = args.pass_
		
	if args.socket:
		dargs.socket = args.socket
	if args.host:
		dargs.host = args.host
	if args.port:
		dargs.port = int(args.port)
		
	if args.type == type_default_none:
		logging.warning( "type='none' may result in inconsistent data dumps" )
		args.type = 'none'
		
	db = mysql.MySQLRip( dargs, DBType[args.type] )

	pipe_to = args.pipe_to
	output_prefix = args.output_prefix
	
	# Output to a directory instead, creating it if necessary
	if args.dump_dir:
		output_prefix = args.dump_dir
		if not output_prefix.endswith( '/' ):
			output_prefix += '/'
		os.makedirs(output_prefix, exist_ok = True)
	
	
	# Use standard compression utitilities
	if args.gzip or args.lzop:
		if not output_prefix:
			raise Exception( 'Compression requires an output option' )
		
		if args.gzip:
			pipe_to = f'gzip > {output_prefix}${{OBJECT_NAME}}.sql.gz'
		elif args.lzop:
			pipe_to = f'lzop > {output_prefix}${{OBJECT_NAME}}.sql.lzop'
			
		output_prefix = None
			
		
	backup(db, output_prefix, args.proc_count, pipe_to )
	
main()
