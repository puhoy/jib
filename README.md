#### JabberIrcBot
a simple(and threaded) jabber/irc bot based on sleekxmpp.

the jabber part is extendable by implementing the XmppBotBase class (see XmppBot in xmpp_bot_impl for examples)

## usage
    python3 jib.py --jid=botjid@domain.com -p "p@s$woRd" --admin=adminjid@domain.com


## installation
    pyvenv-3.4 venv
    source venv/bin/activate
    pip install -r requirements.txt 
    


