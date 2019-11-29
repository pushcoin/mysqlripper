import MySQLdb

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

def main():
	sorted_tables = list_ordered_tables()
	for table in sorted_tables:
		print(table)
	
main()
