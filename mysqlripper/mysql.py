from typing import *

import MySQLdb #type: ignore

from .types import *

class MySQLRip:
	def __init__( self, connection_args : DBConnect ):
		self._connection = None
		self._connection_args = connection_args
		
	def _get_connection(self):
		if self._connection is not None:
			return self._connection

		mc = self._connection_args
		
		cnx = {}
		if mc.user:
			cnx['user'] = mc.user
		if mc.password:
			cnx['passwd'] = mc.password
		if mc.socket:
			cnx['unix_socket'] = mc.socket
		if mc.port:
			cnx['port'] = mc.port
		if mc.host:
			cnx['host'] = mc.host
		
		self._connection = MySQLdb.connect(**cnx)
		return self._connection
		

	def list_ordered_tables(self) -> List[Tuple[str,int]]:
		db = self._get_connection()
		
		cur = db.cursor()
		cur.execute( 'select TABLE_NAME, (INDEX_LENGTH + DATA_LENGTH) as SIZE from information_schema.TABLES where TABLE_SCHEMA="sbtest"')

		tables = [(row[0],row[1]) for row in cur.fetchall()]
		sorted_tables = list(reversed(sorted(tables, key=lambda table: table[1])))
		
		return sorted_tables
		
	def get_dump_cmd(self, table : str, output_prefix : str) -> List[str]:
		cmd = ['mysqldump', self._connection_args.db]
		#'--defaults-file=/longtmp/temp-mysql-pushcoin/mysql/my.cnf',
		
		mc = self._connection_args
		
		if mc.user:
			cmd.append( f'--user={mc.user}' )
		
		if mc.password:
			cmd.append( f'--password={mc.password}')
			
		if mc.socket:
			cmd.append( f'--socket={mc.socket}' )
			
		if mc.port:
			cmd.append( f'--port={mc.port}' )
			
		if mc.host:
			cmd.append( f'--host={mc.host}' )
			
		cmd.append( f'--result-file={output_prefix}{table}.sql' )
		cmd.append( table )
		return cmd
	
	def get_cursor(self):
		return self._get_connection().cursor()
