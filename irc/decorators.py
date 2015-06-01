__author__ = 'meatpuppet'

def op_needed(func):
    '''
    decorates functions to be only executed by admins

    :param func:
    :return:
    '''
    def wrap(bot, room, sender, msg):
        if sender in bot.ops:
            func(bot, sender, msg)
        else:
            # msg.reply('admins only!')
            pass
    return wrap