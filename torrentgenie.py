import os, sys
import urllib.request as urllib2
from bs4 import BeautifulSoup
import re
import pprint
from telegram.ext import Updater, CommandHandler,MessageHandler,Filters
from time import gmtime, strftime
import unicodedata    
from telegram.ext.dispatcher import run_async


from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

def get_mirrors(bot, update):
	proxy_list_url = 'https://thepiratebay-proxylist.org/'
	try:
		print ('Connecting to proxy list...')
		req = urllib2.Request(proxy_list_url, headers={'User-Agent' : "Magic Browser"})
		con = urllib2.urlopen( req ).read()
		soup = BeautifulSoup(con, 'html.parser')
		plist=[]
		#productDivs = soup.findAll('td', attrs={'title' : 'URL'})
		#for div in productDivs:
		#	tmp= div.find('a')['href']
		#	print (tmp)
		#	plist.append(tmp)

		for tmp in soup.findAll('td',attrs={'class': ['url'], 'title': 'URL'}):
			plist.append(tmp.get('data-href'))

		return plist        
	except Exception as e:
		print(e)

def try_connections(proxy_list_urls,bot, update,user_data):
	print(proxy_list_urls)
	for url in proxy_list_urls:
		try:
			print('Trying to connect to '+ url)
			req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
			con = urllib2.urlopen(req)
			print('Connected succssfuly to '+ url)
			update.message.reply_text('Connected succssfuly to '+ url)
			update.message.reply_text('Enter your search query :')
			#create_query(url,bot,update)
			global glob_url
			glob_url=url
			user_data['mykey1']=url
			break
		except(urllib2.HTTPError):
			print ('Could not connect to proxy list')


def create_query(ur,user_input):
	q = user_input.replace(" ", "+")
	global url
	url = ur + "/s/?q="+q+"&page=0&orderby=99"
	print (url)    


def fetchLinkAndTitle():
	req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
	con = urllib2.urlopen(req).read()
	global soup
	soup = BeautifulSoup(con, 'html.parser')
	productDivs = soup.findAll('div', attrs={'class' : 'detName'})
	i=0
	sds=[]
	title=[]
	hrefs=[]
	if(len(productDivs)==0):
		return ["NOT FOUND"] ,["NOTFOUND"]
	for div in productDivs:
		title.append(div.find('a')['title'][12:])
		hrefs.append(glob_url+(div.find('a')['href']))
		i=i+1
	print (i)
	return title,hrefs

def createdict(title,sl,uploaded,link):
	dic={}
	dic["title"]=title
	dic["seeders , leechers "]=sl
	dic["uploaded"]=uploaded
	dic["link"]=link
	return dic
def make_dict_list(t_ar,sl_ar,up_ar,link_ar):
	mlist=[]
	for i in range(len(t_ar)):
		dic=createdict(t_ar[i],sl_ar[i],up_ar[i],link_ar[i])
		mlist.append(dic)
	return mlist

def myprint(i):
	print (title[i])
	print (u[i])
	print (sl[i])
	print (link[i])

def fetchUploader():
	uploader=[]
	productDivs = soup.findAll('font', attrs={'class' : 'detDesc'})
	for div in productDivs:
		uploader.append(div.text)
	print ("done")
	return uploader

def fetchSeeders():
	seederNleecher=[]
	productDivs = soup.findAll('tr')
	for div in productDivs:
		tmp = str(div.findAll('td',attrs={'align' : 'right'}))
		f=[int(x) for x in re.findall("\d+",tmp)]
		seederNleecher.append(f)

	if(len(seederNleecher)>=1):
		del(seederNleecher[0])
	print ("done")
	return seederNleecher

def fetchMagnet(url):
	#print(url)
	magn=[]
	req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
	con = urllib2.urlopen(req).read()
	soup = BeautifulSoup(con, 'html.parser')
	productDivs = soup.findAll('div', attrs={'class' : 'download'})
	for div in productDivs:
		tmp=div.find('a')['href']
	return (tmp)

GET_TEXT=1
GET_TEXT2=2
#@run_async
def start(bot, update,user_data):
	update.message.reply_text("Loading Searching for valid pirateproxy ..you will get a confirmation once searching is completed ")
	plist=get_mirrors(bot,update)
	print(plist)
	try_connections(plist,bot,update,user_data)
	return 1
#@run_async
def get_text(bot, update,user_data):
	user = update.message.from_user
	user_text=update.message.text
	print (user_data['mykey1'])
	create_query(glob_url,update.message.text)
	
	update.message.reply_text('Searching your query ')

	title,link=fetchLinkAndTitle()
	user_data['notfoundflag']=0

	if(title[0]=="NOT FOUND" or link[0]=="NOT FOUND"):
		update.message.reply_text("item not found :(")
		user_data['notfoundflag']=1
		print("notfound")
		return GET_TEXT2
	else:  
		u=fetchUploader()
		sl=fetchSeeders()
		user_data['links']=link
		for i in range(len(title)):
			update.message.reply_text("id:"+str(i)+"\ntitle:"+title[i]+"\nuploader:"+u[i]+"\nseeds and leech:"+str(sl[i])+"\n--------------------")
			
		update.message.reply_text("Enter id number :")
		
	return GET_TEXT2

def get_text2(bot, update,user_data):
	if(user_data['notfoundflag']==0):
		update.message.reply_text("processing your request please wait a while")
		int_user_text=int(update.message.text)
		link=user_data['links']
		st=fetchMagnet(link[int_user_text])
		update.message.reply_text(st)
	return ConversationHandler.END


##@run_async
def cancel(bot, update,user_data):
	user = update.message.from_user
	update.message.reply_text('Cancellation Successful .\n type /start to search again :) ',
							  reply_markup=ReplyKeyboardRemove())

	return ConversationHandler.END

def main():
	TOKEN = ''
	updater = Updater(TOKEN)

	dp = updater.dispatcher
	
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler('start', start,pass_user_data=True)],

		states={
			GET_TEXT: [MessageHandler(Filters.text, get_text,pass_user_data=True),CommandHandler('cancel', cancel,pass_user_data=True)],
			GET_TEXT2: [MessageHandler(Filters.text, get_text2,pass_user_data=True),CommandHandler('cancel', cancel,pass_user_data=True)]
		},
		fallbacks=[CommandHandler('cancel', cancel,pass_user_data=True)]
	)

	dp.add_handler(conv_handler)

	updater.start_polling()
	
	updater.idle()


if __name__ == '__main__':
	main()

			
