__author__ = 'meatpuppet'
#! /usr/bin/env python
#
# Example program using irc.bot.
#
# Joel Rosdahl <joel@rosdahl.net>

"""A simple example bot.

This is an example bot that uses the SingleServerIRCBot class from
irc.bot.  The bot enters a channel and listens for commands in
private messages and channel traffic.  Commands in channel messages
are given by prefixing the text by the bot name followed by a colon.
It also responds to DCC CHAT invitations and echos data sent in such
sessions.

The known commands are:

    stats -- Prints some channel information.

    disconnect -- Disconnect the bot.  The bot will try to reconnect
                  after 60 seconds.

    die -- Let the bot cease to exist.

    dcc -- Let the bot invite you to a DCC CHAT connection.
"""

import irc.bot
import irc.strings

import utility
import logging

import json
import datetime


def get_message_from_event(event):
    return event.arguments[0].split(":", 1)[0].strip()

def get_sender_from_event(event):
    return event.source.split("!", 1)[0]




class IrcBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, server, port=6667, logfile=False, channel=None, in_queue=None, out_queue=None):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.reactor.execute_every(1, self.process_queue)
        self.in_queue = in_queue
        self.out_queue = out_queue

        self.ops = []

        self.logfile = logfile
        self.settings = {}
        self.settings_path = 'settings.json'
        self.load_settings()
        if channel:
            self.settings.get('channels').append(channel)

        logging.basicConfig(level='DEBUG')

        self.xmpp_commands = {
            'irc_join': self.xmpp_command_join,
            'irc_help': self.xmpp_command_help,
            'irc_part': self.xmpp_command_part,
            'irc_add_op': self.xmpp_command_add_op,
            #'op': self.xmpp_command_add_op

        }

        self.irc_commands = {
            '!join': self.irc_command_join,
            '!help': self.irc_command_help,
            '!part': self.irc_command_part,
            '!op': self.irc_command_op,
            '!log': self.irc_command_send_log,
            '!tail': self.irc_command_send_tail,
            '!save': self.irc_command_save_settings,
            '!addop': self.irc_command_add_op
        }


    def load_settings(self):
            with open(self.settings_path, 'r') as settingsfile:
                self.settings = json.loads(''.join(settingsfile))

                """
                server = settings_json.get('server', None)
                channels_to_join = settings_json.get('channels', None)
                """
                self.ops = self.settings.get('ops', None)
                print(self.ops)


    def save_settings(self):
        chans = []
        for channel in self.channels.keys():
            chans.append(channel)
        logging.debug(''.join(self.channels.keys()))
        settings_json = {
            'server': self.connection.server,
            'channels': chans,
            'ops': self.ops
        }
        with open(self.settings_path, 'w') as settingsfile:
            j = json.dumps(settings_json)
            settingsfile.write(j)

    def put_in_queue(self, cmd):
        if self.out_queue:
            self.out_queue.put(cmd)

    def get_from_queue(self):
        if self.in_queue:
            return self.in_queue.get()
        return None

    def process_queue(self):
        #self.connection.notice(self.channel, text='test!')
        cmd = self.get_from_queue()
        if cmd:
            if cmd.get('command') in self.xmpp_commands.keys():
                self.xmpp_commands[cmd.get('command')](cmd)
        #print('now')
        pass

    def give_op(self, conn, event, nick):
        if nick.strip() in self.ops:
            self.connection.mode(event.target, '+o ' + nick)
            #conn.privmsg(event.target, '/MODE +o %s' % nick)
        else:
            conn.privmsg(event.target, 'nick not in operators! (ops are: %s)' % ','.join(self.ops))

    def on_nicknameinuse(self, c, e):
        logging.info('nickname is in use, adding _')
        c.nick(c.get_nickname() + "_")

    def on_join(self, c, e):
        user = get_sender_from_event(e)
        logging.debug('USER:::: %s' % user)
        if user in self.ops:
            self.give_op(c, e, user)
        logging.debug('JOIN::: type: %s, source: %s, target: %s, args: %s'
                      % (e.type, e.source, e.target, ' '.join(e.arguments)))

    def on_welcome(self, c, e):
        #c.join('#*fooo')
        if self.settings.get('channels'):
            for chan in self.settings.get('channels'):
                c.join(chan)

    #def on_privmsg(self, c, e):
    #    self.do_command(e, e.arguments[0])

    def get_logfile_name(self, c, e):
        channel = e.target
        return self.connection.server + '--' + channel + '.log'



    def on_pubmsg(self, c, e):
        """
        logging+triggering commands

        :param c:
        :param e: the event
        :return:
        """
        message = get_message_from_event(e)
        sender = e.arguments[0].split(":", 0)
        logging.debug('event::: type: %s, source: %s, target: %s, args: %s'
                      % (e.type, e.source, e.target, ' '.join(e.arguments)))
        logging.debug('message: %s' % ''.join(message))
        channel = e.target
        if self.logfile:
            with open(self.get_logfile_name(c, e), "a") as log:
                log.write('[%s] %s: %s\n' % (datetime.datetime.now().ctime(), e.source.split('!')[0], message[0]))
        if message.startswith('!'):  # > 1 and irc.strings.lower(message[0]) \
                # == irc.strings.lower(self.connection.get_nickname()):
            self.do_command(e, get_message_from_event(e))
        return

    #def on_dccmsg(self, c, e):
    #    # non-chat DCC messages are raw bytes; decode as text
    #    text = e.arguments[0].decode('utf-8')
    #    c.privmsg("You said: " + text)

    #def on_dccchat(self, c, e):
    #    if len(e.arguments) != 2:
    #        return
    #    args = e.arguments[1].split()
    #    if len(args) == 4:
    #        try:
    #            address = ip_numstr_to_quad(args[2])
    #            port = int(args[3])
    #        except ValueError:
    #            return
    #        self.dcc_connect(address, port)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        print(e.arguments)
        """if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel statistics ---")
                c.notice(nick, "Channel: " + chname)
                users = sorted(chobj.users())
                c.notice(nick, "Users: " + ", ".join(users))
                opers = sorted(chobj.opers())
                c.notice(nick, "Opers: " + ", ".join(opers))
                voiced = sorted(chobj.voiced())
                c.notice(nick, "Voiced: " + ", ".join(voiced))
        elif cmd == "dcc":
            dcc = self.dcc_listen()
            c.ctcp("DCC", nick, "CHAT chat %s %d" % (
                ip_quad_to_numstr(dcc.localaddress),
                dcc.localport))
        else:
        """
        if cmd.split(' ')[0] in self.irc_commands.keys():
            self.irc_commands[cmd.split(' ')[0]](c, e)
        else:
            c.notice(nick, "Not understood: " + cmd)

    """xmpp commands"""
    def xmpp_command_join(self, cmd):
        c = self.connection
        c.join(cmd.get('channel'))

    def xmpp_command_part(self, cmd):
        c = self.connection
        c.part(cmd.get('channel'))

    def xmpp_command_add_op(self, cmd):
        self.ops.append(cmd.get('user'))
        self.save_settings()
        pass

    def xmpp_command_rm_op(self, cmd):
        try:
            self.ops.remove(cmd.get('user'))
            self.save_settings()
        except:
                pass

    def xmpp_command_help(self):
        c = self.connection
    """xmpp commands end"""




    """irc commands"""
    def irc_command_join(self, conn, event):
        if get_sender_from_event(event) not in self.ops:
            conn.privmsg(event.target, 'mh. no.')
        c = self.connection
        cmd = get_message_from_event(event)
        if len(cmd.split(' ')) == 2:
            chan = cmd.split(' ')[1]
            c.join(chan)
        else:
            conn.privmsg(event.target, 'usage: !join <chan>')

    def irc_command_save_settings(self, conn, event):
        if get_sender_from_event(event) not in self.ops:
            conn.privmsg(event.target, 'mh. no.')
        self.save_settings()

    def irc_command_part(self, conn, event):
        #c = self.connection
        if get_sender_from_event(event) not in self.ops:
            conn.privmsg(event.target, 'mh. no.')
        conn.part(event.target, 'bye')
        pass

    def irc_command_add_op(self, conn, event):
        """
        to add an operator permanently

        :param conn:
        :param event:
        :return:
        """
        if get_sender_from_event(event) not in self.ops:
            conn.privmsg(event.target, 'mh. no.')
        cmd = get_message_from_event(event)
        if len(cmd.split(' ')) > 1:
            self.ops.append(cmd.split(' ')[1])
            conn.privmsg(event.target, 'added %s as op' % cmd.split(' ')[1])
        pass

    def irc_command_op(self, conn, event):
        if get_sender_from_event(event) not in self.ops:
            conn.privmsg(event.target, 'mh. no.')
        cmd = get_message_from_event(event)
        if len(cmd.split(' ')) == 2:
            nick = cmd.split(' ')[1]
            self.give_op(conn, event, nick)
        else:
            conn.privmsg(event.target, 'usage: !op <nick>')
        pass

    def irc_command_help(self, conn, event):
        conn.privmsg(event.target, 'available commands: %s' % ', '.join(self.irc_commands.keys()))

    def irc_command_send_log(self, conn, event):
        sender = get_sender_from_event(event)
        receiver = sender
        conn.privmsg(event.target, 'not implemented yet..')
        logging.debug("sendlog event!!")

    def irc_command_send_tail(self, conn, event):
        """
        returns the last n lines

        :param conn:
        :param event:
        :return:
        """
        message = get_message_from_event(event)
        linecnt = 10
        if len(message.split(' ')) > 1:
            try:
                linecnt = int(message.split(' ')[1])
            except:
                pass

        if linecnt > 50:
            conn.privmsg(event.source.split('!')[0], 'too many (>50) lines - i give the last 10...')
            linecnt = 10

        if self.logfile:
            lines = utility.tail(self.get_logfile_name(conn, event), linecnt)
            for line in lines:
                conn.privmsg(event.source.split('!')[0], line.strip())
        else:
            conn.privmsg(event.target, 'sorry, no logfile')
    """irc commands end"""

def main():
    bot = IrcBot('keinbot', 'irc.freenode.net', 6667, logfile=True)
    bot.start()

if __name__ == "__main__":
    main()