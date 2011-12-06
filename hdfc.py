import datetime
import mechanize
import html2text
import cookielib
from BeautifulSoup import BeautifulSoup

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

	def start(self):
		self.br.open('https://m.netbanking.hdfcbank.com/netbanking/')
		self.br.select_form(nr=0)
		self.br.form['fldLoginUserId'] = self.cust_id
		self.br.submit()
		self.state = "started"
		html = self.br.response().read()
		soup =	BeautifulSoup(html)
		# Return authentication info
		try:
			return {
			'phrase':soup.findAll('input',{'name':'fldRSAUserPhrase'})[0]['value'],
			'image':soup.findAll('img')[1]['src']
			}
		except IndexError:
			print 'You should get the secure access setup sometime'

	def login(self,password):
		self.br.select_form('frmLogon')
		self.br.form['fldPassword']=password
		try:
			self.br.find_control('fldCheck').items[0].selected=True
		except mechanize._form.ControlNotFoundError:
			print 'Warning : No secure access'
		self.br.submit()
		self.state = "logged in"
	
	def get_accounts(self):
		if self.state=='logged in':	
			self.state = "out"
			self.br.select_form('frm_menu_accounts_ASM')
			self.br.submit()
			html = self.br.response().read()
			self.ret_to_menu()
			return self.parse_accounts(html)
		pass
	
	def get_account_statement(self,ac_no,st_type,from_date, to_date):
		self.state = "out"
		self.br.select_form('frm_menu_accounts_SIN')
		self.br.submit()
		self.br.select_form('frmTxn')
		self.br.form.set_all_readonly(False)
		self.br.form['fldAcctNo']=ac_no+'++'
		self.br.form['fldNbrStmt']='20'
		self.br.form['fldTxnType'] = 'A'
		self.br.form['radTxnType'] = ['C']
		if st_type!='mini':
			self.br.form['fldFromDate']=from_date.strftime("%d%%2F%m%%2F%Y")
			self.br.form['fldToDate']=to_date.strftime("%d%%2F%m%%2F%Y")
		self.br.submit()
		html = self.br.response().read();
		self.ret_to_menu()
		txns = self.parse_account_statement(html)
		txns=map(self.map_transaction_keys,txns)
		return txns
	
	def map_transaction_keys(self,txn):
		ret = {}
		ret['ref_no'] = txn[u'Cheque/Ref No']
		ret['narration']=txn[u'Narration']
		ret['date']=txn[u'Transaction Date']
		if u'Withdrawal' in txn.keys():
			ret['t_type']='d'
			ret['amount']=float(txn[u'Withdrawal'])
		else:
			ret['t_type']='c'
			ret['amount']=float(txn[u'Deposit'])
		return ret
			
	def logout(self):
		self.br.select_form('frmlogoff')
		self.br.submit()
	
	def parse_accounts(self,html):
		soup = BeautifulSoup(html)
		tables = soup.findAll('table',{'class':'tabdtl'})
		ret=[]
		for table in tables:
			rec = {}
			rows = table.findAll('tr')
			for row in rows:
				cols = row.findAll('td')
				rec.update( { html2text.html2text(cols[0].find(text=True)).strip('\n:') :  html2text.html2text(cols[1].find(text=True)).strip('\n:') })
			ret.append(rec)
		return ret
	
	def parse_account_statement(self,html):
		ret = []
		soup = BeautifulSoup(html)
		for table in soup.findAll('table',{'class':'tableRd'}):
			rec = {}
			for row in table.findAll('tr'):
				cols = row.findAll('td')
				rec.update( { html2text.html2text(cols[0].find(text=True)).strip('\n:') :  html2text.html2text(cols[1].find(text=True)).strip('\n:') })
			ret.append(rec)
		return ret
	
	def ret_to_menu(self):
		self.br.select_form('frmbacktomenu')
		self.br.submit()
		self.state = "logged in"
