__author__ = 'meatpuppet'


import logging

def admin_only(reply_string='admins only!'):
    '''
    decorates functions to be only executed by admins.
    replies reply_string if called by none-admin, or nothing if reply_string is empty

    :param reply_string:
    :return:
    '''
    def dec(func):
        def wrap(bot, sender, msg):
            if sender in bot.admins:
                func(bot, sender, msg)
            else:
                if reply_string:
                    msg.reply(reply_string)
        return wrap
    return dec

def arguments(min=0, max=None, usage=''):
    '''
    decorator for checking argumentcount in msg['body']. '!something one two' has two arguments.
    sends usage back

    :param min:
    :param max:
    :param usage:
    :return:
    '''
    def dec(func):
        def wrap(bot, sender, msg):
            message_split=msg['body'].rstrip().split(' ')
            if len(message_split)-1 >= min:
                if max:
                    if len(message_split)-1 <= max:
                        func(bot, sender, msg)
                        return
            if usage:
                print('sending usage')
                msg.reply('usage: ' + usage).send()
        return wrap
    return dec