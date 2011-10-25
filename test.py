import getpass
from hdfc import hdfc
h = hdfc('6791186')
print h.start()
print h.login(getpass.getpass())
