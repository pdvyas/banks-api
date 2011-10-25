import mechanize
import cookielib

class hdfc:
	def __init__(self,cust_id):
		self.state = "uninitiated"
		self.cust_id = cust_id
		# Browser
		self.br = mechanize.Browser()

		# Cookie Jar
		self.cj = cookielib.LWPCookieJar()
		self.br.set_cookiejar(self.cj)

		# Browser options
		self.br.set_handle_equiv(True)
		self.br.set_handle_gzip(True)
		self.br.set_handle_redirect(True)
		self.br.set_handle_referer(True)
		self.br.set_handle_robots(False)

		# Follows refresh 0 but not hangs on refresh > 0
		self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

		# User-Agent (this is cheating, ok?)
		self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
		self.state = "initiated"

	def start(self,cust_id):
		self.br.open('https://m.netbanking.hdfcbank.com/netbanking/')
		self.br.select_form(nr=0)
		self.br.form['fldLoginUserId'] = self.cust_id
		self.br.submit()
		self.state = "started"
	
	def login(self,password):
		self.state = "logged in"
	
	def get_accounts(self):
		pass
	
	def get_account_statement(self,ac_no):
		pass
