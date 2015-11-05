import datetime

'''
Module to have a centralized way of printing information
in both the test environment and the normale working environment
'''
INFO = "info"
ERROR = "error"
CRITICAL = "critical"

'''
Test environment is on or not
'''
TEST_MODUS = False

'''
Print a message in normal working order
Suppress messages of the test environment
'''
def log_error(type_log, str_log):
    if not TEST_MODUS:
        print_error(type_log, str_log)

'''
Print a message of the test environment
Suppress messages of the normal working order
'''
def log_error_test(type_log, str_log):
    if TEST_MODUS:
        print_error(type_log, str_log)

'''
Print an error
'''
def print_error(type_log, str_log):
    now_str = datetime.datetime.now().strftime("[%H:%M:%S:%f %d-%m-%Y]")
    error_str = now_str + "(" + type_log +")" + ": " + str_log
    print error_str
