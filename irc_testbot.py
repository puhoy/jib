#!/usr/bin/env python3

"""https://www.sevadus.tv/forums/index.php?/topic/774-simple-python-irc-bot/"""
import re
import socket

import threading


import logging
import select
import datetime


class IrcBot(threading.Thread):
    def __init__(self, nick, server, port=6667, in_queue=None, out_queue=None, logfile=None):
        threading.Thread.__init__(self)

        logging.basicConfig(level=logging.DEBUG)
        logging.info('started logging!')
        self.nick = nick
        self.server = server
        self.port = port
        self.con = None
        self.running = False

        self.in_queue = in_queue
        self.out_queue = out_queue

        self.commands = {'!test': self.command_test,
                         '!help': self.command_help
                         }

        self.logfile = logfile

        #self.start()

    def send_pong(self, msg):
        logging.debug('sending pong to %s' % self.server)
        self.con.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))

    def send_message(self, chan, msg):
        self.con.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))
        if self.logfile:
            with open(chan+'--'+self.logfile, "a") as log:
                log.write('[%s] %s: %s\n' % (datetime.datetime.now().ctime(), self.nick, msg))

    def send_nick(self, nick):
        self.con.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))

    def join_channel(self, chan):
        self.con.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))

    def part_channel(self, chan):
        self.con.send(bytes('PART %s\r\n' % chan, 'UTF-8'))

    def send_pass(self, password):
        self.con.send(bytes('PASS %s\r\n' % password, 'UTF-8'))

    def send_user(self, nick):
        # USER <username> <hostname> <servername> :<realname>
        self.con.send(bytes('USER  %s %s %s :%s\r\n' % (nick, nick, nick, nick), 'UTF-8'))

    def connect(self):
        self.con = socket.socket()
        self.con.connect((self.server, self.port))
        logging.debug(self.con)
        #self.send_pass('')
        self.send_nick(self.nick)
        self.send_user(self.nick)
        #logging.info('connected to %s:%s as %s' % (self.server, self.port, self.nick))
        #send_pass(PASS)
    # --------------------------------------------- End Functions ------------------------------------------------------


    # --------------------------------------------- Start Helper Functions ---------------------------------------------
    def get_sender(self, msg):
        result = ""
        for char in msg:
            if char == "!":
                break
            if char != ":":
                result += char
        return result

    def get_message(self, msg):
        result = ""
        i = 3
        length = len(msg)
        room = msg[2]
        while i < length:
            result += msg[i] + " "
            i += 1
        result = result.lstrip(':')
        return room, result

    def parse_message(self, room, msg):
        if len(msg) >= 1:
            msg = msg.split(' ')
            if msg[0] in self.commands:
                self.commands[msg[0]](room, msg)
    # --------------------------------------------- End Helper Functions -----------------------------------------------

    def command_test(self, room, msg):
        print('message: %s' % msg)
        self.send_message(room, 'testing some stuff')

    def command_help(self, room, msg):
        self.send_message(room, 'available commands: %s' % ','.join(self.commands.keys()))
        pass

    def run(self):
        logging.debug('running...')
        self.connect()
        data = ""
        self.running = True
        self.con.setblocking(0)
        while self.running:
            if self.in_queue:
                while not self.in_queue.empty():
                    cmd = self.in_queue.get(True, 0.1)
                    if cmd.get('command', None) == 'join':
                        self.join_channel(cmd.get('room'))
                        logging.info('joining %s' % cmd.get('room'))

            ready_to_read, ready_to_write, in_error = select.select(
                  [self.con],  # potential_readers,
                  [self.con],  # potential_writers,
                  [self.con],  # potential_errs,
                  0.1  # timeout
                  )
            for socket in ready_to_read:
                data = data+decode(socket.recv(1024))
                data_split = str.split(data, '\n')
                data = data_split.pop()

                for line in data_split:
                    line = str.rstrip(line)
                    line = str.split(line)
                    if line[0] == 'PING':
                        self.send_pong(line[1])
                    if len(line) > 1:
                        if line[1] == 'PRIVMSG':
                            sender = self.get_sender(line[0])
                            room, message = self.get_message(line)
                            if self.logfile:
                                with open(room+'--'+self.logfile, "a") as log:
                                    log.write('[%s] %s: %s\n' % (datetime.datetime.now().ctime(), sender, message))
                            self.parse_message(room, message)



if __name__ == '__main__':
    bot = IrcBot('ubik__', 'irc.freenode.net')
    bot.start()

''' from http://inamidst.com/whits/code/hebe/irc3.py '''
def decode(data):
   for encoding in ('utf-8', 'iso-8859-1', 'cp1252'):
      try:
          #logging.debug('trying: %s' % encoding)
          return data.decode(encoding)
      except UnicodeDecodeError: continue