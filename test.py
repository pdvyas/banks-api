import getpass
from hdfc import hdfc
h = hdfc('1572332')
h.start()
h.login(getpass.getpass())
print h.get_accounts()
h.logout()
