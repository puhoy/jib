#!/usr/bin/env python3

"""https://www.sevadus.tv/forums/index.php?/topic/774-simple-python-irc-bot/"""

import socket

import threading


import logging
import select
import datetime

import json

from utility import tail

from .decorators import op_needed



class IrcBot(threading.Thread):
    def __init__(self, nickname, server, port=6667, password=None, in_queue=None, out_queue=None, logfile=None, channel=None):
        threading.Thread.__init__(self)

        logging.basicConfig(level=logging.DEBUG)
        logging.info('started logging!')
        self.nickname = nickname
        self.server = server
        self.port = port
        self.con = None
        self.running = False

        self.channels = []

        self.password = password

        self.ops = []

        self.settings = {}
        self.settings_path = 'settings.json'

        self.in_queue = in_queue
        self.out_queue = out_queue

        self.xmpp_commands = {
            #'irc_join': self.xmpp_command_join,
            #'irc_help': self.xmpp_command_help,
            #'irc_part': self.xmpp_command_part,
            #'irc_add_op': self.xmpp_command_add_op,
            #'op': self.xmpp_command_add_op

        }

        self.irc_commands = {
            '!join': self.irc_command_join,
            '!help': self.irc_command_help,
            '!part': self.irc_command_part,
            '!op': self.irc_command_give_op,
            '!log': self.irc_command_send_log,
            '!tail': self.irc_command_send_tail,
            '!save': self.irc_command_save_settings,
            '!addop': self.irc_command_add_op
        }

        self.load_settings()
        if channel:
            self.settings.get('channels').append(channel)
        self.logfile = logfile

        #self.start()

    def load_settings(self):
        try:
            with open(self.settings_path, 'r') as settingsfile:
                self.settings = json.loads(''.join(settingsfile))

                """
                server = settings_json.get('server', None)
                channels_to_join = settings_json.get('channels', None)
                """
                self.ops = self.settings.get('ops', None)
                print(self.ops)
        except:
            pass

    def save_settings(self):
        chans = []
        for channel in self.channels.keys():
            chans.append(channel)
        logging.debug(''.join(self.channels.keys()))
        settings_json = {
            'server': self.server,
            'channels': chans,
            'ops': self.ops
        }
        with open(self.settings_path, 'w') as settingsfile:
            j = json.dumps(settings_json)
            settingsfile.write(j)

    def process_queue(self):
        cmd = self.get_from_queue()
        if cmd:
            if cmd.get('command') in self.xmpp_commands.keys():
                self.xmpp_commands[cmd.get('command')](cmd)

    def put_in_queue(self, cmd):
        if self.out_queue:
            self.out_queue.put(cmd)

    def get_from_queue(self):
        if self.in_queue:
            try:
                cmd = self.in_queue.get(block=False)
            except:
                cmd = None
            return cmd

    def after_motd(self):
        #logging.debug('got motd')
        for channel in self.settings.get('channels'):
            self.join_channel(channel)

    def send_pong(self, msg):
        logging.debug('sending pong to %s' % self.server)
        self.con.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))

    def get_logfile_name(self, channel):
        return self.server + '--' + channel + '.log'

    def send_message(self, chan, msg):
        self.con.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))
        if self.logfile:
            with open(self.get_logfile_name(chan), "a") as log:
                log.write('[%s] %s: %s\n' % (datetime.datetime.now().ctime(), self.nickname, msg))

    def give_op(self, nick, room):
        self.con.send(bytes('MODE %s +o %s\r\n' % (room, nick), 'UTF-8'))

    def send_nick(self, nick):
        self.con.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))

    def join_channel(self, chan):
        self.con.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))
        logging.debug('joining %s' % chan )
        self.channels.append(chan)

    def part_channel(self, chan):
        self.con.send(bytes('PART %s\r\n' % chan, 'UTF-8'))
        self.channels.remove(chan)

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
        self.send_nick(self.nickname)
        self.send_user(self.nickname)
        #logging.info('connected to %s:%s as %s' % (self.server, self.port, self.nick))
        if self.password:
            self.send_pass(self.password)
    # --------------------------------------------- End Functions ------------------------------------------------------


    # --------------------------------------------- Start Helper Functions ---------------------------------------------







    def get_sender(self, msg):
        result = ""
        print('getting sender from: %s' % msg)
        for char in msg:
            if char == "!":
                break
            if char != ":":
                result += char
        logging.debug('got sender: %s' % result)
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

    def parse_message(self, room, sender, msg):
        if len(msg) >= 1:
            msg = msg.split(' ')
            if msg[0] in self.irc_commands:
                logging.debug('got command: %s' % msg)
                self.irc_commands[msg[0]](room, sender, msg)

    def send_tail(self, channel, to, lines):
        if lines > 50:
            self.send_message(to, 'too many (>50) lines - i give the last 10...')
            lines = 10

        if self.logfile:
            lines = tail(self.get_logfile_name(channel), lines)
            for line in lines:
                self.send_message(to, line)
        else:
            self.send_message(channel, 'sorry, no logfile')

    # --------------------------------------------- End Helper Functions -----------------------------------------------

    def command_test(self, room, sender, msg):
        print('message: %s' % msg)
        self.send_message(room, 'testing some stuff')

    def irc_command_help(self, room, sender, msg):
        self.send_message(room, 'available commands: %s' % ', '.join(self.irc_commands.keys()))
        pass

    def irc_command_give_op(self, room, sender, msg):
        nick = sender
        if nick in self.ops:
            self.give_op(nick, room)
        else:
            self.send_message(room, '%s shouldnt be op' % nick)

    @op_needed
    def irc_command_join(self, room, sender, msg):
        help = 'usage: !join <channel>'
        if len(msg) >= 2:
            channel = msg[1]
            self.join_channel(channel)
        else:
            self.send_message(room, help)


    @op_needed
    def irc_command_part(self, room, sender, msg):
        self.part_channel(room)

    def irc_command_send_log(self, room, sender, msg):
        self.send_message(room, 'not implemented')

    def irc_command_send_tail(self, room, sender, msg):
        help = 'usage: !tail <lines>'
        lines = 10
        if len(msg) == 3:
            try:
                lines = int(msg[2])
            except:
                self.send_message(room, help)

        self.send_tail(room, sender, lines)
        #self.send_message(room, 'not implemented')

    @op_needed
    def irc_command_save_settings(self, room, sender, msg):
        self.send_message(room, 'not implemented')

    @op_needed
    def irc_command_add_op(self, room, sender, msg):
        self.send_message(room, 'not implemented')


    def run(self):
        logging.debug('running...')
        self.connect()
        data = ""
        self.running = True
        self.con.setblocking(0)
        while self.running:
            self.process_queue()

            ready_to_read, ready_to_write, in_error = select.select(
                  [self.con],  # potential_readers,
                  [self.con],  # potential_writers,
                  [self.con],  # potential_errs,
                  0.1  # timeout
                  )
            for socket in ready_to_read:
                data = data+decode(socket.recv(1024))
                if data:
                    logging.debug('raw data: %s' % data)
                data_split = str.split(data, '\n')
                data = data_split.pop()

                for line in data_split:
                    if len(line.split(':')) == 3:
                        if line.split(':')[2].strip() == "End of /MOTD command.":
                            self.after_motd()
                    line = str.rstrip(line)
                    line = str.split(line)
                    if line[0] == 'PING':
                        self.send_pong(line[1])
                    if len(line) > 1:
                        if line[1] == 'PRIVMSG':
                            sender = self.get_sender(line[0])
                            room, message = self.get_message(line)
                            '''logging'''
                            if self.logfile:
                                with open(self.get_logfile_name(room), "a") as log:
                                    log.write('[%s] %s: %s\n' % (datetime.datetime.now().ctime(), sender, message))
                            '''handle commands'''
                            self.parse_message(room, sender, message)

"""End of /MOTD command."""

if __name__ == '__main__':
    bot = IrcBot('ubikasdf', 'irc.freenode.net', logfile=True)
    bot.start()

''' from http://inamidst.com/whits/code/hebe/irc3.py '''
def decode(data):
   for encoding in ('utf-8', 'iso-8859-1', 'cp1252'):
      try:
          #logging.debug('trying: %s' % encoding)
          return data.decode(encoding)
      except UnicodeDecodeError: continue