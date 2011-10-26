import getpass
from hdfc import hdfc
import pprint 
h = hdfc(raw_input('Enter cust_id : '))
print "Here are your Secure Access credentials"
print h.start()
h.login(getpass.getpass())
pprint.pprint(h.get_accounts())
h.logout()
