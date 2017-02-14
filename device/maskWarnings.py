#!python3

class MaskingComplaint(Exception):
	pass
	
def createWarning(message):
	res = "\033[93mWarning!\033[0m "
	return res+message
	
def createError(message):
	res = "\033[91mError!\033[0m "
	return res+message

