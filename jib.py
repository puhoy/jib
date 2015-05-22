__author__ = 'meatpuppet'

import sys
import logging
import getpass
from optparse import OptionParser
import queue

from xmpp_bot import XmppBot
from irc_bot import IrcBot

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


irc_networks = {}
import threading

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
        xmpp_bot.process(blocking=False)
        #print("Done")
    else:
        print("Unable to connect.")
    logging.info('going into loop...')

    run = True
    while run:
        #logging.debug('waiting for commands...')
        try:
            cmd = xmpp_bot.out_queue.get(True, 1)
        except Exception as e:
            cmd = ''
        if cmd:
            print('got command!')
            logging.debug('command: %s' % cmd)
            cmd_str = cmd.get('command', None)
            if cmd_str == 'irc_connect':
                logging.info('got connect to %s' % cmd.get('server'))
                server = cmd.get('server', None)
                port = cmd.get('port', 6667)
                nickname = cmd.get('nickname', 'keinbot')
                irc_networks[cmd.get('server')] = IrcBot(nickname=nickname, server=server, port=port,
                                                         in_queue=queue.Queue(), logfile=True)
                threading.Thread(
                    target=irc_networks[cmd.get('server')].start
                ).start()
            elif cmd_str:
                if cmd_str.startswith('irc_'):
                    logging.debug('command: %s' % cmd)
                    try:
                        irc_networks[cmd.get('server')].in_queue.put(cmd)
                    except Exception as e:
                        errstr = 'something went wrong: %s (%s)' % (e, sys.exc_info()[0])
                        logging.info(errstr)
                        pass
            if cmd_str == 'die':
                for network in irc_networks.values():
                    network.disconnect('killed')
                print('bye!')
                xmpp_bot.disconnect()
                run = False
