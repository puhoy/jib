__author__ = 'meatpuppet'

from .xmpp_bot_base import XmppBotBase
from .decorators import admin_only, arguments


class XmppBot(XmppBotBase):
    def __init__(self, jid, password, in_queue=None, out_queue=None, admin=''):
        XmppBotBase.__init__(self, jid, password, in_queue=in_queue, out_queue=out_queue)

        self.commands = {#'!test': self.command_test,
                     '!help': self.command_help,
                     '!irc_join': self.command_irc_join,
                     '!irc_connect': self.command_irc_connect,
                     '!irc_part': self.command_irc_part,
                     '!irc_add_op': self.command_irc_add_op,
                     '!die': self.command_die
                     }

        self.admins = []
        if admin:
            self.admins.append(admin)

    ''' irc commands '''
    @admin_only
    @arguments(min=1, max=2, usage="!irc_connect <server> [nickname]")
    def command_irc_connect(self, sender, msg):
        '''connect to an irc network
        '''
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

    @admin_only
    @arguments(min=2, max=2, usage='!irc_join <network> <channel>')
    def command_irc_join(self, sender, msg):
        '''
        join a channel on a network

        :param sender:
        :param msg:
        :return:
        '''
        server = msg['body'].split(' ')[1]
        channel = msg['body'].split(' ')[2]
        msg.reply("joining %s!" % (channel)).send()
        cmd = {
            'command': 'irc_join',
            'server': server,
            'channel': channel
        }
        self.out_queue.put(cmd)

    @admin_only
    @arguments(min=2, max=2, usage='!irc_add_op <network> <username>')
    def command_irc_add_op(self, sender, msg):
        '''
        add irc-op to operator list (irc network specific!)

        :param sender:
        :param msg:
        :return:
        '''
        server = msg['body'].strip().split(' ')[1]
        user = msg['body'].strip().split(' ')[2]
        cmd = {
            'command': 'irc_add_op',
            'server': server,
            'user': user
        }
        self.out_queue.put(cmd)

    @admin_only
    @arguments(min=2, max=2, usage='!irc_part <network> <channel>')
    def command_irc_part(self, sender, msg):
        '''
        leave a channel

        :param sender:
        :param msg:
        :return:
        '''
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
                        mbody="available commands: %s" % (', '.join(self.commands.keys())),
                        mtype='chat')

    @admin_only
    @arguments(min=0, max=0, usage='!die')
    def command_die(self,  sender, msg):
        '''
        shut down

        :param sender:
        :param msg:
        :return:
        '''
        cmd = {'command': 'die'}
        self.out_queue.put(cmd)
            #msg.reply("Thanks for sending\n%(body)s" % msg).send()
