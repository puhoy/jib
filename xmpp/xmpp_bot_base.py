__author__ = 'meatpuppet'
#!/usr/bin/env python
# -*- coding: utf-8 -*-


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


class XmppBotBase(sleekxmpp.ClientXMPP):
    """
    xmpp bot base inspired by
    http://io.drigger.com/posts/201410252029-using-thread-based-sleekxmpp-together-with-the-asyncio-event-loop-in-python-3.html
    (and built out of the echo bot example)

    in_queue: input queue.
        if you need this, you should implement the handle_input_queue function.

    out_queue: output queue

    commands: holds a table of commands you want to define.
    the commands you define are triggered in the message handle.
        example:
            self.commands = {'help': self.send_help}

            def help(self, sender, msg):
                msg.return('that should help you')

    admins: a list of admins. used by the admins_only decorator. (see decorators.py)
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

        self.commands = {}  # to implement
        self.admins = {}  # to implement

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

        '''add a scheduler to handle the input queue'''
        if self.in_queue:
            self.scheduler.add('in_queue_handling', 1, self.handle_input_queue, repeat=True)

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
            #if not msg['from'].bare in self.admins:
            #    #msg.reply("ok, you tested. msg:\n%(body)s" % msg).send()
            #    logging.debug('message from %s (no admin)' % msg['from'].bare)
            #    return
            if msg['body'].split(' ')[0] in list(self.commands.keys()):
                if len(msg['body']) >= 1:
                    command = msg['body'].split(' ')[0]
                    if command in self.commands:
                        self.commands[command](msg['from'].bare, msg)
                    else:
                        # msg.reply("cmd not found...").send()
                        pass

    def handle_input_queue(self):
        '''
        you can use this method to handle your input queue.
        this function will be called every second,
        so you can use it to do input-queue unrelated stuff also.
        (see the snippet below...)
        '''
        '''
        if self.in_queue:
            try:
                cmd = self.in_queue.get(block=False)
                ...
        '''
        raise NotImplementedError("Please Implement this method")
