import functools
def log(text=''):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args,**kw):
			print "start %s %s() " %(text, func.__name__)
			res = func(*args,**kw)
			print "end"
			return res
		return wrapper
	return decorator

@log()
def now():
	print '2013-12-25';



now()

