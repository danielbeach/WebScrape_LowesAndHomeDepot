'''
SQL TABLES NEEDED
CREATE TABLE dbo.StoreAddress (StoreNum INT, StoreName NVARCHAR(30), Address1 NVARCAR(30), 
								City NVARCHAR(30), State NVARCHAR(10), PostalCode NVARCHAR(30),
								Country NVARCHAR(30))
'''
from urllib.request import Request, urlopen
import json
import pyodbc
import time

class Address(): #create address class with its attributes
	def __init__(self, storeNumber):
		self.storeNumber = str(storeNumber).replace("{'",'').replace("'}",'')
		self.Address1 = ''
		self.Address2 = ''
		self.City = ''
		self.State = ''
		self.PostalCode = ''
		self.Country = ''
	
	def set_address1(self, slice, storeName): #simply split what we need for each attribute
		if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
			start = '"street":"'
			end = '"}'
			self.Address1 = find_between( slice.encode(), start.encode(), end.encode() )
		elif storeName == "LOWE'S COMPANIES, INC.":
			start = slice.split('<li>',1)[-1]
			end = start.split('</li>',1)[0]
			self.Address1 = end
	
	def set_city(self, slice, storeName):
		if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
			start = '"city":"'
			end = '","street'
			self.City = find_between( slice.encode(), start.encode(), end.encode() )
		elif storeName == "LOWE'S COMPANIES, INC.":
			start = slice.split('<li>',1)[-1]
			middle = start.split('<li>',1)[-1]
			end = middle.split(',',1)[0]
			self.City = end
		
	def set_state(self, slice, storeName):
		if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
			start = '"state":"'
			end = '","country"'
			self.State = find_between( slice.encode(), start.encode(), end.encode() )
		elif storeName == "LOWE'S COMPANIES, INC.":
			start = slice.split(', ',1)[-1]
			end = start.split(' ',1)[0]
			self.State = end
		
	def set_postalcode(self, slice, storeName):
		if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
			start = '"postalCode":"'
			end = '"'
			self.PostalCode = find_between( slice.encode(), start.encode(), end.encode() )
		elif storeName == "LOWE'S COMPANIES, INC.":
			start = slice.split('<li>',1)[-1]
			middle = start.split('<li>',1)[-1]
			end = middle.split('</li>',1)[0]
			end = end[-5:]
			self.PostalCode = end
		
	def set_country(self, slice, storeName):
		if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
			start = '"country":"'
			end = '","city"'
			self.Country = find_between( slice.encode(), start.encode(), end.encode() )
		elif storeName == "LOWE'S COMPANIES, INC.":
			self.Country = ''

def getStoreList(): #go get em'
	storeList = [] #empty list
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=YOURSERVER;DATABASE=YOURDATABASE;UID=USERID;PWD=PASSWORD') #connect
	cursor = cnxn.cursor() #open cursor
	query = cursor.execute("SELECT StoreNum FROM dbo.StoreAddress WHERE Address1 IS NULL")
	for row in cursor.fetchall(): #got'em
		storeList.append({row.StoreNum}) #add'em
	cnxn.close() #clean up
	return storeList
	
def buildURL(storeNumber,storeName): #make up full url to hit.
	if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
		url = 'https://www.homedepot.com/l/search/' + str(storeNumber).replace("{'",'').replace("'}",'') + '/full/'
	elif storeName == "LOWE'S COMPANIES, INC.":
		url = ''
	return url

def makeRequest(url,storeNumber,storeName):
	if storeName == "LOWE'S COMPANIES, INC.":
		req = Request('http://lowes.know-where.com/lowes/cgi/site?site=' + str(storeNumber).replace("{'",'').replace("'}",'') + '&design=default&lang=en&option=&mapid=us', headers={'User-Agent': 'Mozilla/5.0'})
		html = urlopen(req).read()
		time.sleep(3) # Lowes is too smart, blocks python and too many requests.
	elif storeName == "THE HOME DEPOT":
		with urlopen(url) as response:
			html = response.read()
	return html

def sliceEm(requestedHTML,storeNumber,storeName):
	if storeName == 'THE HOME DEPOT' or storeName == 'HOME DEPOT CANADA':
		start = '"storeId":"' + str(storeNumber).replace("{'",'').replace("'}",'') + '",'
		end = ',"coordinates":'
		slice = find_between( requestedHTML, start.encode(), end.encode() )
		slice = str(slice).replace("b'","")
	elif storeName == "LOWE'S COMPANIES, INC.":
		start = '<li>Store Number:'
		end = '/ul>'
		slice = find_between( requestedHTML, start.encode(), end.encode() )
		slice = str(slice).replace("b'","")
	return slice

def putAddy(Address1,City,State,PostalCode,Country,storeNumber):
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=YOURSERVER;DATABASE=YOURDATABASE;UID=USERID;PWD=PASSWORD') #connect
	cursor = cnxn.cursor() #open cursor
	query = cursor.execute("UPDATE SysproReporting.dbo.StoreAddress SET Address1 = ?, City = ?, State = ?, PostalCode = ?, Country = ? WHERE StoreNum = ?",Address1,City,State,PostalCode,Country,storeNumber)
	cnxn.commit()
	cnxn.close()

def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def main():
	storeList = getStoreList() #make list of store numbers
	for storeNumber in storeList: #for each store make url request
		storeName = "LOWE'S COMPANIES, INC."
		url = buildURL(storeNumber, storeName) #build url with storeNumber
		requestedHTML = makeRequest(url,storeNumber, storeName)
		slice = sliceEm(requestedHTML,storeNumber, storeName)
		addy = Address(storeNumber) #create instance of address
		addy.set_address1(slice, storeName)
		addy.set_city(slice, storeName)
		addy.set_state(slice, storeName)
		addy.set_postalcode(slice, storeName)
		addy.set_country(slice, storeName)
		putAddy(addy.Address1,addy.City,addy.State,addy.PostalCode,addy.Country,addy.storeNumber)
		print("finished one")
	
if __name__ == "__main__":
	main()