__author__ = 'meatpuppet'

import sys
import logging
import getpass
from optparse import OptionParser
import queue

from xmpp_bot import XmppBot
from irc_testbot_old import IrcBot

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


irc_networks = {}

if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    # Setup the EchoBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp_bot = XmppBot(opts.jid, opts.password, in_queue=queue.Queue(), out_queue=queue.Queue())
    xmpp_bot.register_plugin('xep_0030') # Service Discovery
    xmpp_bot.register_plugin('xep_0004') # Data Forms
    xmpp_bot.register_plugin('xep_0060') # PubSub
    xmpp_bot.register_plugin('xep_0199') # XMPP Ping

    # If you are working with an OpenFire server, you may need
    # to adjust the SSL version used:
    # xmpp.ssl_version = ssl.PROTOCOL_SSLv3
    #xmpp.XMPP_CA_CERT_FILE = None
    xmpp_bot.reconnect_max_attempts=2
    # If you want to verify the SSL certificates offered by a server:
    #xmpp.ca_certs = "./kwoh.de.crt"



    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp_bot.connect():
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp_bot.process(threaded=True, blocking=False)
        #print("Done")
    else:
        print("Unable to connect.")
    logging.info('going into loop...')


    while True:
        while not xmpp_bot.out_queue.empty():
            cmd = xmpp_bot.out_queue.get(True, 0.1)
            if cmd.get('command', None) == 'irc_connect':
                logging.info('got connect to %s' % cmd.get('server'))
                irc_networks[cmd.get('server')] = IrcBot(nick='ubik__', server=cmd.get('server'), port=6667, in_queue=queue.Queue(), logfile=cmd.get('server')+'.log')
                irc_networks[cmd.get('server')].start()
            elif cmd.get('command', None) == 'irc_join':
                # irc_networks[cmd.get('server')].join(cmd.get('room'))
                logging.info('got join to %s' % cmd.get('room'))
                irc_networks[cmd.get('server')].in_queue.put(
                    {'command': 'join',
                     'room': cmd.get('room')
                     }
                )
            elif cmd.get('command', None) == 'irc_add_op':
                irc_networks[cmd.get('server')].in_queue.put(
                    {'command': 'add_op',
                     'user': cmd.get('user')
                     }
                )
            elif cmd.get('command', None) == 'irc_rm_op':
                irc_networks[cmd.get('server')].in_queue.put(
                    {'command': 'rm_op',
                     'user': cmd.get('user')
                     }
                )