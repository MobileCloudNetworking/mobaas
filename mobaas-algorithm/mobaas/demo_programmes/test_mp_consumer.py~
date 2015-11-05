import signal
import sys

from mobaas.demo_programmes import test_consumer
from mobaas.demo_programmes import config

from mobaas.common import error_logging as err

test_consumer_obj = None

'''
MP Consumer. Uses a test consumer with some small configuration.
'''

'''
Shut down cleanly on a CTRL+C signal
'''
def shutdown(sig_num, sf):
    test_consumer_obj.close()
    sys.exit(0)


'''
Start up the test consumer
'''
def main():
    global test_consumer_obj
    test_consumer_obj = test_consumer.TestConsumer("MP Test Consumer", config.TEST_MP_MESSAGES, config.WAIT_BETWEEN_SENDS_MP)

    signal.signal(signal.SIGINT, shutdown)

    if test_consumer_obj.start():
        err.log_error(err.INFO, "Test Consumer started!")
        test_consumer_obj.go_to_work()
    else:
        err.log_error(err.CRITICAL, "Could not start the Test Consumer! Quitting...")

'''
Only call if module is called directly
'''
if __name__ == "__main__":
    main()
