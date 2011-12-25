import datetime
import mechanize
import html2text
import cookielib
import dateutil.parser
import hashlib
import re
from BeautifulSoup import BeautifulSoup
from common import genid

class Bank:
	__bank__= 'hdfc'
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
			acs = self.parse_accounts(html)
			acs = map(self.map_account_keys,acs)
			return acs
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
		ac_id = genid({'acno': ac_no, 'bank' : self.__bank__ })
		txns = [self.map_transaction_keys(x,ac_id) for x in txns]
		txns = [self.process_txn(x) for x in txns]
		return txns

	def process_txn(self,txn):
		
		narr = txn['narration']
		ttype = narr[:3]
		ret = {
			'ttype' : ttype
		}

		def atw():
			match = re.search(r'ATW-(\d*).-(.*)',narr)
			ret['card'] = match.group(1)
			ret['place'] = match.group(2)

		def ndw():
			match = re.search(r'NDW-(\d*).*-(.*)',narr)
			ret['card'] = match.group(1)
			ret['place'] = match.group(2)

		def pos():
			match = re.search(r'POS (\d*) (.*)',narr)
			ret['card'] = match.group(1)
			ret['merchant'] = match.group(2)

		def xfer():
			match = re.search(r'IB FUNDS TRANSFER.*-(\d*)',narr)
			ret['merchant'] = match.group(1)

		def chq():
			match = re.search(r'Chq.*-.*-(.*)',narr)
			ret['merchant'] = match.group(1)
		
		pat = {
				'ATW' : atw,
				'NDW' : ndw,
				'POS' : pos,
				'Chq' : chq,
				'IB ' : xfer
		}

		try:
			pat[ttype]()
		except KeyError:
			pass
		txn.update(ret)
		return txn

	
	def map_account_keys(self,ac):
		ret = {}
		ret['ac_no']=ac[u'Account Number']
		ret['bank'] = self.__bank__
		ret['id'] = genid(ret)
		ret['balance']=float(ac[u'Available Balance'])
		return ret
	
	def map_transaction_keys(self,txn,ac_id):
		ret = {}
		ret['ac_id'] = ac_id
		ret['ref_no'] = txn[u'Cheque/Ref No']
		ret['narration']=txn[u'Narration']
		ret['bal']=txn[u'Balance']
		ret['date']=dateutil.parser.parse(txn[u'Transaction Date']).date()
		if u'Withdrawal' in txn.keys():
			ret['t_type']='d'
			ret['amount']=float(txn[u'Withdrawal'])
		else:
			ret['t_type']='c'
			ret['amount']=float(txn[u'Deposit'])
		ret['id'] = genid(ret)
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
