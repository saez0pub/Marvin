#!/usr/bin/python
# -*- coding: utf-8 -*-
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import datetime
import time
import configparser
import json
from random import randint
import os
import codecs

 
class Bot(irc.bot.SingleServerIRCBot):
  def __init__(self):
    path = os.getcwd()
    self.configfile = path + "/Marvin.cfg"
    self.config = configparser.ConfigParser()
    self.getConfig()
    irc.bot.SingleServerIRCBot.__init__(self, [("ircserver", 6667)],
                                       self.conf['nick'], "Je suis un bot super sympa.")
    irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer
    self.lastmessage=""
    self.lastmessage2=""
    self.lastmessage3=""
    self.lastAntiSpam = 0
  def getConfig(self):
    self.config = configparser.ConfigParser()
    self.config.read(self.configfile)
    self.conf = dict()
    self.conf['nick'] = self.config.get('config','nick')
    self.conf['chan'] = self.config.get('config','chan')
    self.conf['channels'] = [self.conf['chan']]
    self.conf['phraseWelcome'] = self.config.get('config','phrase_welcome')
    self.conf['insultes'] = json.loads(self.config.get('config','insultes'))
    self.conf['punch'] = json.loads(self.config.get('config','punch'))
    self.conf['admins'] = json.loads(self.config.get('config','admins'))
    self.premierrepeat = self.config.get('config','premierrepeat')
    self.deuxiemerepeat = self.config.get('config','deuxiemerepeat')
    itemsmotcle = self.config.items('motcle')
    self.conf['motcle'] = {}
    for mot, reponse in itemsmotcle:
      self.conf['motcle'] = dict(self.conf['motcle'], **{mot:reponse})
  def on_nicknameinuse(self, c, e):
     c.nick(c.get_nickname() + "_")
     self.conf['nick'] = self.conf['nick'] + "_"
  def on_welcome(self, connection, event):
    connection.join(self.conf['chan'])
    self.print_to_out ("welcome", self.conf['chan'], self.conf['nick'], "/join " + self.conf['chan'])
    self.do_privmsg(connection, self.conf['chan'], self.conf['phraseWelcome'])
  def on_mode(self, connection, event):
    self.getConfig()
    source = event.source
    auteur = event.source.nick
    canal = event.target
    args = event.arguments
    mode = args[0]
    try:
      target = args[1]
    except IndexError:
      target = None
    if canal == self.conf['chan'] and mode == "+o" and target == self.conf['nick']:
      self.do_privmsg(connection, canal, "Merci " + auteur)
  def on_pubmsg(self, connection, event):
    self.getConfig()
    auteur = event.source.nick
    source = event.source
    chan = event.target
    message = event.arguments[0]
    hostname = event.source.host
    sleepTime = randint(10,30)-1
    messageResp = ""
    self.print_to_out ("pubmsg", chan, auteur, message)
    if auteur != self.conf['nick']:
      if (source in self.conf['admins']):
        connection.mode(chan, " +o " + auteur)
      if "!"+self.conf['nick'].lower() in message.lower():
        messageResp = "et "+message[8:100] + " !"
      elif "trolled" in message.lower() or "trolled" == auteur.lower() or "trolled'pc" == hostname:
        if 1 == randint(1,6): 
          time.sleep(sleepTime)
          self.do_privmsg(connection, chan, "ok trolled !")
      elif self.conf['nick'].lower() in  message.lower():
        insulte = 0
        for mot in self.conf['insultes']:
          if mot in message.lower() :
            insulte = 1
            action = randint(0,len(self.conf['punch']))-1
            messageResp = "Merci de rester poli " + auteur +" !"
            punch = self.conf['punch'][action].replace('$auteur$', auteur)
            if punch != self.conf['punch'][action]:
              self.do_privmsg(connection, chan, punch)
            else:
              connection.action(chan, punch + auteur)
            break
        if insulte == 0:
          if "bonjour " in message.lower() and self.conf['nick'].lower() in message.lower():
             if auteur == "C-3PO":
               messageResp = "Salut copain !"
             else:
               messageResp = "Bonjour " + auteur
          elif "merci "+ self.conf['nick'].lower() in message.lower() or self.conf['nick'].lower()+" merci" in message.lower() or self.conf['nick'].lower()+": merci" in message.lower():
            messageResp = "De rien."
          else:
            reponseOK = 0
            for mot, reponse in self.conf['motcle'].items():
              if mot in message.lower():
                reponseArr=reponse.split('|||')
                messageResp = reponseArr[randint(0,len(reponseArr)-1)].replace('$auteur$',auteur)
                reponseOK = 1
            if reponseOK == 0:
              essai = randint(1,10)
              if essai > 8:
                messageResp = "Je n'ai pas compris."
              elif essai > 6:
                messageResp = "C'est pas faux."
              elif  essai > 4:
                messageResp = "lol"

      else:
        for mot, reponse in self.conf['motcle'].items():
          if mot in message.lower():
            reponseArr=reponse.split('|||')
            messageResp = reponseArr[randint(0,len(reponseArr)-1)].replace('$auteur$',auteur)
      #print ("messageResp Avant Anti spam : " + messageResp)
      if time.time() - self.lastAntiSpam < 3600:
        if messageResp == self.lastmessage3:
          messageResp = ""
        elif messageResp == self.lastmessage2:
          self.lastmessage3 = messageResp
          messageResp = self.deuxiemerepeat
        elif messageResp == self.lastmessage:
          self.lastmessage2 = messageResp
          messageResp = self.premierrepeat
        else:
          self.lastmessage = ""
          self.lastmessage2 = ""
          self.lastmessage3 = ""
      else:
        self.lastmessage = ""
        self.lastmessage2 = ""
        self.lastmessage3 = ""
      #print ("messageResp : " + messageResp)
      #print ("self.lastmessage : " + self.lastmessage)
      #print ("self.lastmessage2 : " + self.lastmessage2)
      #print ("self.lastmessage3 : " + self.lastmessage3)
      if messageResp is not "":
        self.do_privmsg(connection, chan, messageResp)
        self.lastmessage = messageResp
  def on_join(self, connection, event):
    #print ("connection")
    #print (vars(connection))
    #print ("eventent")
    #print (vars(event))
    chan = event.target
    source = event.source
    auteur = event.source.nick
    if (auteur in self.conf['admins']):
      connection.mode(chan, " +o " + auteur)
      if auteur == "otherbot":
        self.do_privmsg(connection, chan, "Salut copain !")
  def on_privmsg(self, connection, event):
    chan = self.conf['chan']
    source = event.source
    auteur = event.source.nick
    message = event.arguments[0]
    arguments = message.split(" ")
    source = event.source
    trouve = 0
    isAdmin = 0
    self.print_to_out ("privmsg", self.conf['nick'], auteur, message)
    if message == "stats":
        trouve = 1
        for chname, chobj in self.channels.items():
          self.do_privmsg(connection, auteur, "--- Channel statistics ---")
          self.do_privmsg(connection, auteur, "Channel: " + chname)
          users = list(chobj.users())
          users.sort()
          self.do_privmsg(connection, auteur, "Users: " + ", ".join(users))
          opers = list(chobj.opers())
          opers.sort()
          self.do_privmsg(connection, auteur, "Opers: " + ", ".join(opers))
          voiced = list(chobj.voiced())
          voiced.sort()
          self.do_privmsg(connection, auteur, "Voiced: " + ", ".join(voiced))
    else:
      for admin in self.conf['admins']:
        if (admin == source):
          self.do_privmsg(connection, auteur, "Vous etes admin" )
          isAdmin = 1
          trouve = 1
          if '&config' in arguments[0]:
            self.do_privmsg(connection, auteur, "relecture conf : " )
            self.getConfig()
            for conf, value in self.conf.items():
              self.do_privmsg(connection, auteur, conf + '====================' )
              self.print_to_out ("privmsg", self.conf['nick'], self.conf['nick'],value)
              if isinstance(value, (list, tuple, dict)):
                self.do_privmsg(connection, auteur, str(len(value)) + " valeurs configurées")
              else:
                self.do_privmsg(connection, auteur, value )
              time.sleep(0.1)
          elif '&dire' in arguments[0]:
            self.do_privmsg(connection, auteur, "dire : " + message[5:].strip())
            self.do_privmsg(connection, chan, message[5:])
          elif '&action' in arguments[0]:
            connection.action(chan, message[7:].strip())
          elif '&mode' in arguments[0]:
            connection.mode(chan, message[5:])
          elif '&carrement!' in arguments[0]:
            if len(arguments) > 1:
              temps = int(arguments[1])
            else:
              temps = 10
            connection.part(self.conf['chan'], "A dans " + str(temps) + "secondes !")
            time.sleep(temps)
            connection.join(self.conf['chan'])
          elif '&exit' in arguments[0]:
            connection.disconnect("A la prochaine bye")
    if message == "help" or message == "aide":
      self.do_privmsg(connection, auteur, "Commandes : ")
      self.do_privmsg(connection, auteur, "aide : affiche cette aide ")
      self.do_privmsg(connection, auteur, "help : affiche cette aide ")
      self.do_privmsg(connection, auteur, "stats : affiche les stats ")
      if isAdmin == 1:
        self.do_privmsg(connection, auteur, "&config : relit la configuration et l'affiche")
        self.do_privmsg(connection, auteur, "&dire<message> : envoie un message dans "+self.conf['chan'])
        self.do_privmsg(connection, auteur, "&action<message> : envoie un /me dans "+self.conf['chan'])
        self.do_privmsg(connection, auteur, "&mode : envoie un /mode dans "+self.conf['chan'])
        self.do_privmsg(connection, auteur, "&carrement!<x> : envoie un /part dans "+self.conf['chan']+" et se reconnecte x secondes après, par défaut 10")
        self.do_privmsg(connection, auteur, "&exit : deconnecte le bot")
    elif trouve == 0 and isAdmin == 0:
        self.do_privmsg(connection, auteur, "Ho !!! Je suis un bot !!!! Et vous n'etes pas admin !" + auteur)
    elif trouve == 0 and isAdmin == 1:
        self.do_privmsg(connection, auteur, "Pas compris: " + message +", essayez aide ou help")
  def on_kick(self, connection, event):
    connection.join(self.conf['chan'])
  def do_privmsg(self, connection, dest, message):
    self.print_to_out("privmsg", dest, self.conf['nick'], message)
    connection.privmsg(dest, message)
  def print_to_out(self, type, chan, auteur, message):
    i = datetime.datetime.now()
    print ("%s : %s : %s : %s : %s" % (i, type, chan, auteur, message))

if __name__ == "__main__":
    Bot().start()
