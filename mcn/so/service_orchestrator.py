import logging


def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()


class Execution(object):
    """
    Interface to the CC methods. No decision is taken here on the service
    """

    def __init__(self, token, tenant):
        super(Execution, self).__init__()
        raise NotImplementedError()

    def design(self):
        raise NotImplementedError()

    def deploy(self):
        raise NotImplementedError()

    def provision(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

    def dispose(self):
        raise NotImplementedError()

    def state(self):
        raise NotImplementedError()


class Decision(object):

    def __init__(self):
        super(Decision, self).__init__()
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()