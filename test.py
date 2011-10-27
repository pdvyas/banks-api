import getpass
from hdfc import hdfc
import pprint 
h = hdfc(raw_input('Enter cust_id : '))
print "Here are your Secure Access credentials"
print h.start()
h.login(getpass.getpass())
try:
#	pprint.pprint(h.get_accounts())
	pprint.pprint(h.get_account_statement('02751000048940'))
except Exception, e:
	h.logout()
	raise e
h.logout()
