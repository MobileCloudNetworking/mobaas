import datetime

from mobaas.mobaas_protocol import message_objects
from mobaas.common import support

'''
All of the messages where the mp consumer will cycle through
'''
mp_start_datetime_1 = datetime.datetime(year=2009, month=12, day=4, hour=04, minute=29, second=0)
mp_start_datetime_2 = datetime.datetime(year=2009, month=12, day=4, hour=04, minute=29, second=0)
mp_start_datetime_3 = datetime.datetime(year=2009, month=12, day=7, hour=22, minute=51, second=0)
mp_start_datetime_4 = datetime.datetime(year=2009, month=12, day=8, hour=20, minute=36, second=0)
TEST_MP_MESSAGES = [# message_objects.MPSingleUserRequest(5980, mp_start_datetime_1.time(), mp_start_datetime_1.date(), 1 * 60, 12963)
                   #, message_objects.MPSingleUserRequest(5980, mp_start_datetime_2.time(), mp_start_datetime_2.date(), 20 * 60, 12963)
                   #, message_objects.MPSingleUserRequest(5963, mp_start_datetime_3.time(), mp_start_datetime_3.date(), 55 * 60, 3729)
                   #, message_objects.MPSingleUserRequest(5974, mp_start_datetime_4.time(), mp_start_datetime_4.date(), 48 * 60, 1535)
                   # message_objects.MPMultiUserRequest(0000, "23:30", "Monday", 5),
		   # message_objects.MPMultiUserRequest(0000, "23:30", "Tuesday", 5),
	           # message_objects.MPMultiUserRequest(0000, "23:30", "Wednesday", 5),
                   # message_objects.MPMultiUserRequest(0000, "23:30", "Thursday", 5),
                   # message_objects.MPMultiUserRequest(0000, "23:30", "Friday", 5),
                   # message_objects.MPMultiUserRequest(0000, "23:30", "Saturday", 5),
                    message_objects.MPMultiUserRequest(0000, "17:10", "Monday", 10)
                   ]

'''
All of the messages where the bp consumer will cycle through
'''
bp_start_datetime = support.from_unix_timestamp_to_datetime(1415976546)
TEST_BP_MESSAGES = [message_objects.BPSingleLinkRequest(1, bp_start_datetime.time(), bp_start_datetime.date(), 12)]

'''
How long to wait between sending each message within the consumer in seconds
'''
WAIT_BETWEEN_SENDS_MP = 1500 #In seconds
WAIT_BETWEEN_SENDS_BP = 20 #In seconds

'''
Configuration of the names for the test_maas db layout.
Used within test_db_layout
'''
TEST_MAAS_DB = "test_maas"
TEST_MAAS_USER_INFO_TABLE = "test_user_info"
TEST_MAAS_FLOW_DATA_TABLE = "test_flow_data"
TEST_MAAS_LINK_CAPACITY_DATA_TABLE = "test_link_capacity"

'''
Configuration to the test file directories for each part of the
test data
'''
FILEPATH_TO_TEST_FILES_DATA_USER_DIRECTORY = "./mobaas/test_data/test_user"
FILEPATH_TO_TEST_FILES_DATA_FLOW_DIRECTORY = "./mobaas/test_data/test_flow"
FILEPATH_TO_TEST_FILES_DATA_LINK_CAP_DIRECTORY = "./mobaas/test_data/test_link_cap"
