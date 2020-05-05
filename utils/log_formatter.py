

class LogFormatter:
    """ Handles formatting for logs """

    def __init__(self):
        self.padding = 0
        self.fmt = "<green>{time:HH:mm:ss}</>  |  <cyan>{function}:{line}{extra[padding]}</>  |  " \
                   "<level>{message}</>\n{exception}"

    def format(self, record):

        length = len("{name}:{function}:{line}".format(**record))
        self.padding = max(self.padding, length)
        record["extra"]["padding"] = " " * (self.padding - length)

        return self.fmt
