__author__ = 'meatpuppet'
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys


import sleekxmpp
import logging

import queue

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

admins = ['jan@kwoh.de']




class XmppBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot that will echo messages it
    receives, along with a short thank you message.
    """

    def __init__(self, jid, password, in_queue=None, out_queue=None):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self.message)

        self.in_queue = in_queue
        self.out_queue = out_queue

        self.commands = {#'!test': self.command_test,
                         '!help': self.command_help,
                         '!irc_join': self.command_irc_join,
                         '!irc_connect': self.command_irc_connect,
                         '!irc_part': self.command_irc_part,
                         '!irc_add_op': self.command_irc_add_op
                         }


    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        self.get_roster()

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['type'] in ('chat', 'normal'):
            if not msg['from'].bare in admins:
                #msg.reply("ok, you tested. msg:\n%(body)s" % msg).send()
                logging.debug('message from %s (no admin)' % msg['from'].bare)
                return
            if msg['body'].startswith('!'):
                if len(msg['body']) >= 1:
                    command = msg['body'].split(' ')[0]
                    if command in self.commands:
                        self.commands[command](msg['from'].bare, msg)
                    else:
                        msg.reply("cmd not found...").send()

    #def command_irc(self, sender, msg):
    #    self.send_message(mto=sender,
    #                    mbody="irc networks: %s" % (','.join(self.irc_networks.keys())),
    #                    mtype='chat')

    def command_irc_connect(self, sender, msg):
        if len(msg['body'].strip().split(' ')) < 2:
           msg.reply("usage: !irc_connect <server> (<nickname>)").send()
        else:
            server = msg['body'].split(' ')[1]
            cmd = {
                'command': 'irc_connect',
                'server': server
            }
            '''if nickname given'''
            if len(msg['body'].strip().split(' ')) == 3:
                cmd['nickname'] = msg['body'].strip().split(' ')[2]

            self.out_queue.put(cmd)
            msg.reply("connecting to %s!" % (server)).send()


    def command_irc_join(self, sender, msg):
        server = msg['body'].split(' ')[1]
        channel = msg['body'].split(' ')[2]
        msg.reply("joining %s!" % (channel)).send()
        cmd = {
            'command': 'irc_join',
            'server': server,
            'channel': channel
        }
        self.out_queue.put(cmd)



    def command_irc_add_op(self, sender, msg):
        server = msg['body'].strip().split(' ')[1]
        user = msg['body'].strip().split(' ')[2]
        cmd = {
            'command': 'irc_add_op',
            'server': server,
            'user': user
        }
        self.out_queue.put(cmd)
        #

    def command_irc_part(self, sender, msg):
        server = msg['body'].strip().split(' ')[1]
        channel = msg['body'].strip().split(' ')[2]
        msg.reply("leaving %s!" % (channel)).send()
        cmd = {
            'command': 'irc_part',
            'server': server,
            'channel': channel
        }
        self.out_queue.put(cmd)

    def command_help(self, sender, msg):
        self.send_message(mto=sender,
                        mbody="available commands: %s" % (','.join(self.commands.keys())),
                        mtype='chat')
            #msg.reply("Thanks for sending\n%(body)s" % msg).send()
