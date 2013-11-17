import logging

class logger(object):
    @staticmethod
    def who(who, _in = None):
        if _in:
            return '@(%s)>{%s}: ' % (_in, who)
        return '>{%s}: ' % who

    #defaults to info log
    @staticmethod
    def log(who, msg, *args):
        logging.info(logger.who(who) + msg, *args)

    @staticmethod
    def debug(who, _in, msg, *args):
        logging.debug(logger.who(who, _in) + msg, *args)

    @staticmethod
    def warn(who, msg, *args):
        logging.warning(logger.who(who) + msg, *args)

    @staticmethod
    def info(who, msg, *args):
        logger.log(who, msg, *args)

    @staticmethod
    def error(who, _in, msg, *args):
        logging.error(logger.who(who, _in) + msg, *args)
