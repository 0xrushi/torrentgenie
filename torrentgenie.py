import os, sys
from bs4 import BeautifulSoup
import re
import pprint
from telegram.ext import Updater, CommandHandler,MessageHandler,Filters
from time import gmtime, strftime
import unicodedata    
from telegram.ext.dispatcher import run_async

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import logging

import configparser
import requests


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

GET_TEXT = 1
SEARCH = 2
GET_TEXT2 = 3

def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


class TorrentGenie:
    def __init__(self):
        self.url=""
        self.glob_url=""
        self.session = requests.session()
        # Tor uses the 9050 port as the default socks port
        #self.session.proxies = {'http': 'socks5://127.0.0.1:9050','https': 'socks5://127.0.0.1:9050'}
    def get_mirrors(self ,proxy_list_url = 'https://thepiratebay-proxylist.org/' ):
        try:
            print ('Connecting to proxy list...')
            req = (self.session).get(proxy_list_url, headers={'User-Agent' : "Magic Browser"}).text
            soup = BeautifulSoup(req, 'html.parser')
            plist=[]
            #productDivs = soup.findAll('td', attrs={'title' : 'URL'})
            #for div in productDivs:
            #    tmp= div.find('a')['href']
            #    print (tmp)
            #    plist.append(tmp)

            for tmp in soup.findAll('td',attrs={'class': ['url'], 'title': 'URL'}):
                plist.append(tmp.get('data-href'))
            return plist        
        except Exception as e:
            print(e)


    def try_connections(self, proxy_list_urls,bot, update,user_data): #2
        print(proxy_list_urls)
        for url in proxy_list_urls:
            try:
                print('Trying to connect to '+ url)
                req = self.session.get(url, headers={'User-Agent' : "Magic Browser"}).text
                print('Connected succssfuly to '+ url)
                update.message.reply_text('Connected succssfuly to '+ url)
                update.message.reply_text('Enter your search query :')
                #global glob_url
                self.glob_url=url
                user_data['mykey1']=url
                break
            except Exception as e:
                print ('Could not connect to proxy list')


    def create_query(self, ur,user_input, i):
        q = user_input.replace(" ", "+")
        url = ur + "/s/?q="+q+"&page="+str(i)+"&orderby=99"
        print (url)    
        return url


    def fetchLinkAndTitle(self, urlx):
        req = self.session.get(urlx, headers={'User-Agent' : "Magic Browser"}).text
        #print("request in fetchLinkAndTitle is "+req)
        #print("url in fetchLinkAndTitle is "+urlx)
        self.soup = BeautifulSoup(req, 'html.parser')
        productDivs = self.soup.findAll('div', attrs={'class' : 'detName'})
        i=0
        title=[]
        hrefs=[]
        if(len(productDivs)==0):
            return ["NOT FOUND"] ,["NOTFOUND"]
        for div in productDivs:
            title.append(div.find('a')['title'][12:])
            hrefs.append(self.glob_url+(div.find('a')['href']))
            i=i+1
        print (i)
        return title, hrefs

    def createdict(self, title,sl,uploaded,link):
        dic={}
        dic["title"]=title
        dic["seeders , leechers "]=sl
        dic["uploaded"]=uploaded
        dic["link"]=link
        return dic
    def make_dict_list(self, t_ar,sl_ar,up_ar,link_ar):
        mlist=[]
        for i in range(len(t_ar)):
            dic=self.createdict(t_ar[i],sl_ar[i],up_ar[i],link_ar[i])
            mlist.append(dic)
        return mlist

#    def myprint(self, i):
#        print (title[i])
#        print (u[i])
#        print (sl[i])
#        print (link[i])

    def fetchUploader(self, soup):
        uploader=[]
        productDivs = soup.findAll('font', attrs={'class' : 'detDesc'})
        for div in productDivs:
            uploader.append(div.text)
        print ("done")
        return uploader

    def fetchSeeders(self, soup):
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

    def fetchMagnet(self, url):
        #print(url)
        #print("url in fetchmagnet is "+ url)
        req = self.session.get(url, headers={'User-Agent' : "Magic Browser"}).text
        soup = BeautifulSoup(req, 'html.parser')
        productDivs = soup.findAll('div', attrs={'class' : 'download'})
        for div in productDivs:
            tmp=div.find('a')['href']
        return tmp

    @run_async
    def start(self, bot, update,user_data):
        self.__init__()
        update.message.reply_text("Loading Searching for valid pirateproxy ..you will get a confirmation once searching is completed ")
        plist=self.get_mirrors()
        print(plist)
        while not plist:
            plist=self.get_mirrors()
        self.try_connections(plist,bot,update,user_data)
        return GET_TEXT
    @run_async
    def get_text(self,bot, update,user_data, i=0): #enter something to search
        user = update.message.from_user
        print("in here")
#        user_text=update.message.texts
        print (user_data['mykey1'])
        self.url=self.create_query(self.glob_url,update.message.text, i)
        
        tmp= self.search_query(bot,update,user_data)
        return GET_TEXT2

    def search_query(self,bot,update,user_data):
        bot.send_message(chat_id=update.effective_chat.id, text="Searching your query")
        print("url in search_query  "+self.url)
        title,link=self.fetchLinkAndTitle(self.url)
        user_data['notfoundflag']=0
        
        if(title[0]=="NOT FOUND" or link[0]=="NOT FOUND"):
            update.message.reply_text("item not found :( type /cancel to exit.")
            user_data['notfoundflag']=1
            print("notfound")
            return GET_TEXT2
        else:  
            u=self.fetchUploader(self.soup)
            sl=self.fetchSeeders(self.soup)
            user_data['links']=link
            for i in range(len(title)):
                keyboard = [[InlineKeyboardButton("Get Link", callback_data=str(i))]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                #button = InlineKeyboardButton("Get Link", )
                #update.message.reply_text("id:"+str(i)+"\ntitle:"+title[i]+"\nuploader:"+u[i]+"\nseeds and leech:"+str(sl[i])+"\n--------------------", reply_markup=reply_markup)
                bot.send_message(chat_id=update.effective_chat.id, text= "id:"+str(i)+"\ntitle:"+title[i]+"\nuploader:"+u[i]+"\nseeds and leech:"+str(sl[i])+"\n--------------------", reply_markup=reply_markup)
                
            #update.message.reply_text("Loading complete, click on Get link of your choice:")
            bot.send_message(chat_id=update.effective_chat.id, text= "Loading complete, click on Get link of your choice:")
                             
            button_list = [
            InlineKeyboardButton("Previous page", callback_data="pre"),
            InlineKeyboardButton("Next Page", callback_data="next")]
            #InlineKeyboardButton("row 2", callback_data="now")]

            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
            bot.send_message(chat_id=update.effective_chat.id, text=".", reply_markup=reply_markup)

        return "tmp"

    
    def button(self, bot,  update):
        query = update.callback_query
        query.edit_message_text(text="Selected option: {}".format(query.data))
    
    def get_text2(self,bot, update, user_data):
        query = update.callback_query
        print("get_text2 "+query.data)
        
        if query.data=="next":
            ind=self.url.index("&page=")
            ind=ind+6
            turl = list(self.url)
            turl[ind]=str(int(turl[ind])+1)
            self.url=''.join(turl)
            tmp= self.search_query(bot,update,user_data)
            return GET_TEXT2
        elif query.data=="pre":
            ind=self.url.index("&page=")
            ind=ind+6
            turl = list(self.url)
            turl[ind]=str(int(turl[ind])-1)
            self.url=''.join(turl)
            tmp= self.search_query(bot,update,user_data)
            return GET_TEXT2
        #print("damm "+query.data)
        if(user_data['notfoundflag']==0):
            bot.send_message(chat_id=update.effective_chat.id, text="processing your request please wait a while")
            #update.message.reply_text("processing your request please wait a while")
            #print(type(query.data))
            int_user_text=int(query.data)
            link=user_data['links']
            st=self.fetchMagnet(link[int_user_text])
            bot.send_message(chat_id=update.effective_chat.id, text=st)
            bot.send_message(chat_id=update.effective_chat.id, text= 'You may click any other get magnet button or type /cancel to END and /start to start again  :) ')
            #update.message.reply_text('',reply_markup=ReplyKeyboardRemove())
        
        return GET_TEXT2


    @run_async
    def cancel(self,bot, update,user_data):
        self.__init__()
        user = update.message.from_user
        update.message.reply_text('Cancellation Successful .\n type /start to search again :) ',
                                  reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END


    def main(self):
        configParser = configparser.RawConfigParser()
        configParser.readfp(open(r'config.txt'))
        TOKEN = configParser.get('TOKEN', 'tok')
        REQUEST_KWARGS=    {'proxy_url': 'socks5://localhost:9050/'}

        updater = Updater(TOKEN,  request_kwargs=REQUEST_KWARGS)

        dp = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start,pass_user_data=True)],

            states={
                GET_TEXT: [MessageHandler(Filters.text, self.get_text,pass_user_data=True),CommandHandler('cancel', self.cancel,pass_user_data=True)],
                GET_TEXT2: [CallbackQueryHandler(self.get_text2,pass_user_data=True),CommandHandler('cancel', self.cancel,pass_user_data=True)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel,pass_user_data=True)]
        )
        
        dp.add_handler(conv_handler)
        dp.add_handler(CommandHandler('cancel', self.cancel, pass_user_data=True))
        #dp.add_handler(CommandHandler('cancel', self.cancel))
        #dp.add_handler(CallbackQueryHandler(self.get_text2,pass_user_data=True))


        updater.start_polling()

        updater.idle()


if __name__ == '__main__':
    tg=TorrentGenie()

    tg.main()

            
