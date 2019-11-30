from enum import Enum

class DBConnect:
	def __init__(self):
		self.user : Optional[str] = None
		self.password : Optional[str] = None
		self.socket : Optional[str] = None
		self.port : Optional[int] = None
		self.host : Optional[str] = None
		self.db : str = ''
		
class DBType(Enum):
	none = 0
	master = 1
	slave = 2
	
