import time
import datetime
import signal
import sys

from mobaas import config as central_config

from mobaas.common import error_logging as err
from mobaas.common import support

from mobaas.socket_connections import server_connections as serv_con

from mobaas.database_connections import db_connections as db_con

from mobaas.demo_programmes import test_db_layout
from mobaas.demo_programmes import config

from mobaas.mobaas_protocol import mobaas_protocol
from mobaas.mobaas_protocol import message_objects

'''
A test supplier/MaaS. Handles any request for data that comes in from MOBaaS
and tries to return all the data matching the request.

This program starts by first reading all of the test data into the database
Then it tries to handle all requests coming in before shutting down gracefully
by a CTRL+C signal.

Database tables are created/destroyed at initialisation/shutdown
'''
class TestSupplier:
    def __init__(self, name, db_name):
        self.server = serv_con.Server(name, central_config.MaaS_port, central_config.MaaS_hostname)
        self.dbcc = db_con.DBConnectionCollection(name)
        self.dbcc.create_multiple_connections([db_name])

    def start(self):
        return self._start_server() and self._start_database()

    def _start_server(self):
        return self.server.start()

    def _start_database(self):
        r1 = self.dbcc.start_all_connections()
        r2 = self._start_table( test_db_layout.MaaSUserMobilityInformation
                              , config.FILEPATH_TO_TEST_FILES_DATA_USER_DIRECTORY
                              , TestSupplier._read_in_user_info
                              )
        r3 = self._start_table( test_db_layout.MaaSFlowData
                              , config.FILEPATH_TO_TEST_FILES_DATA_FLOW_DIRECTORY
                              , TestSupplier._read_in_flow_data
                              )
        r4 = self._start_table( test_db_layout.MaaSLinkCapacityData
                              , config.FILEPATH_TO_TEST_FILES_DATA_LINK_CAP_DIRECTORY
                              , TestSupplier._read_in_link_cap_data
                              )

        return r1 and r2 and r3 and r4

    def _start_table(self, layout_class, directory_path_to_test_data, func_line_to_obj_args):
        result = True

        if not layout_class.table_exists(self.dbcc):
            result = layout_class.create_table(self.dbcc)

            if layout_class.table_exists(self.dbcc):
                err.log_error(err.INFO, "Starting to read in " + str(layout_class) + " test data...")
                filepaths = support.directory_to_list_of_filepaths(directory_path_to_test_data)
                result = result and layout_class.fill_table_from_files(self.dbcc, None, filepaths, func_line_to_obj_args)

                if result:
                    err.log_error(err.INFO, "Succesfully read in all " + str(layout_class) + " test data!")
                else:
                    err.log_error(err.CRITICAL, "Could not read in all the test data for " + str(layout_class) + "...")

        return result

    @staticmethod
    def _read_in_user_info(filename, extension, words):

        dt = datetime.datetime.strptime(" ".join([words[0], words[1], words[2], words[3], words[4]]),"%a %b %d %H:%M:%S %Y")
        time = dt.time()
        date = dt.date()
        user_id = int(filename[-4:])
        cell_id = int(words[5])

        return [user_id, time, date, cell_id]

    @staticmethod
    def _read_in_flow_data(filename, extension, words):

        link_id = 1
        start_time = int(words[1])
        end_time = int(words[3])
        num_of_packets = float(words[7])
        num_of_bytes = float(words[8])

        return [link_id, start_time, end_time, words[5], words[6], num_of_packets, num_of_bytes]

    @staticmethod
    def _read_in_link_cap_data(filename, extension, words):
        link_id = int(words[0])
        capacity = int(words[1])

        return [link_id, capacity]

    def go_to_work(self):
        while True:
            self._handle_accept_phase()
            self._handle_read_phase()
            self._handle_send_phase()
            self._handle_destroy_unusable_connections_phase()
            time.sleep(0.01)

    def _handle_accept_phase(self):
        self.server.accept_connections()

    def _handle_read_phase(self):
        self.server.read_from_connections()
        connections = self.server.check_for_messages(mobaas_protocol.contains_complete_message)

        for connection in connections:
            messages = connection.consume_all_complete_messages(mobaas_protocol.contains_complete_message, mobaas_protocol.first_complete_message_ends_at)
            for message in messages:
                message_object = mobaas_protocol.parse_message(message)
                handle_incoming_mobaas_message(self.dbcc, connection, message_object)

    def _handle_send_phase(self):
        self.server.send_to_connections()

    def _handle_destroy_unusable_connections_phase(self):
        self.server.destroy_all_unusable_connections()

    def close(self):
        r1 = self._close_server()
        r2 = self._close_database()

        return r1 and r2

    def _close_server(self):
        self.server.broadcast_close(message_objects.EndConversation(self.server.name + " is being closed."))
        return self.server.close()

    def _close_database(self):
        r1 = test_db_layout.MaaSFlowData.delete_table(self.dbcc)
        r2 = test_db_layout.MaaSUserMobilityInformation.delete_table(self.dbcc)
        r3 = test_db_layout.MaaSLinkCapacityData.delete_table(self.dbcc)

        r4 = self.dbcc.close_all_connections()

        return r1 and r2 and r3 and r4

'''
How to handle an incoming mobaas message.
Delegates the work to the correct handle_incoming_x_message
function depending on the type of message

Each handle_incoming_x_message function tries to retrieve
the data before returning the correct answer.

This function than sends that answer to MOBaaS
'''
def handle_incoming_mobaas_message(dbcc, connection, msg):
    answer = None
    connection_is_closed = False
    err.log_error(err.INFO, "Handling request: " + str(msg))
    if isinstance(msg, message_objects.MaaSSingleUserDataRequest):
        answer = handle_user_data_request(dbcc, msg)
    elif isinstance(msg, message_objects.MaaSSingleLinkDataRequest):
        answer = handle_flow_data_request(dbcc, msg)
    elif isinstance(msg, message_objects.MaaSSingleLinkCapacityRequest):
        answer = handle_link_capacity_request(dbcc, msg)
    elif isinstance(msg, message_objects.EndConversation):
        err.log_error(err.INFO, "Connection " + str(connection) + " is requested to end because: " + msg.reason)
        connection.close()
        connection_is_closed = True
    else:
        err.log_error(err.ERROR, "Received a message of type " + str(type(msg)) + " that is not supported.")
        err.log_error(err.ERROR, "Message: " + str(msg))

    if not connection_is_closed:
        if not answer:
            answer = message_objects.Error(204, "Could not find the requested data")

        err.log_error(err.INFO, "Returning answer of type: " + str(answer.__class__))
        connection.add_message(answer)


def handle_user_data_request(dbcc, msg):
    err.log_error(err.INFO, "Found a request for user data")
    start_date_time = datetime.datetime.combine(msg.start_date, msg.start_time)
    end_date_time =  start_date_time + datetime.timedelta(seconds=msg.time_span)
    end_time = end_date_time.time()
    end_date = end_date_time.date()

    conditions = [ ("user_id", "=", msg.user_id)
                 , ("date", ">=", msg.start_date)
                 , ("date", "<=", end_date)
                 ]

    user_information_objects = test_db_layout.MaaSUserMobilityInformation.retrieve_objects(dbcc, conditions)

    valid_user_information_objects = []
    #Limit between requested start and end time
    for user_info_obj in user_information_objects:
        user_info_date_time = datetime.datetime.combine(user_info_obj.date, user_info_obj.time)

        if start_date_time <= user_info_date_time <= end_date_time:
            valid_user_information_objects.append(user_info_obj)

    #Limit to the correct resolution
    reduced_user_information_objects = test_db_layout.MaaSUserMobilityInformation.reduce_to_time_resolution(valid_user_information_objects, msg.time_resolution)

    err.log_error(err.INFO, "Sending " + str(len(reduced_user_information_objects)) + " rows of user data")

    return test_db_layout.MaaSUserMobilityInformation.construct_maas_single_user_data_answer(msg.user_id, msg.start_date, msg.start_time, msg.time_span, reduced_user_information_objects)

def handle_flow_data_request(dbcc, msg):
    err.log_error(err.INFO, "Found a request for flow data")
    end_date_time = datetime.datetime.combine(msg.start_date, msg.start_time) + datetime.timedelta(seconds=msg.time_span)
    start_time_unix_ms = support.to_unix_timestamp_ms_from_date_and_time(msg.start_date, msg.start_time)
    stop_time_unix_ms = support.to_unix_timestamp_ms_from_date_and_time(end_date_time.date(), end_date_time.time())

    db_flow_data_objects = test_db_layout.MaaSFlowData.retrieve_flow_data(dbcc, msg.link_id, start_time_unix_ms, stop_time_unix_ms)

    err.log_error(err.INFO, "Sending " + str(len(db_flow_data_objects)) + " rows of flow data")

    return test_db_layout.MaaSFlowData.construct_maas_single_link_answer(msg.link_id, db_flow_data_objects)

def handle_link_capacity_request(dbcc, msg):
    answer = None
    conditions = [ ("link_id", "=", msg.link_id)
                 ]

    link_capacity_objects = test_db_layout.MaaSLinkCapacityData.retrieve_objects(dbcc, conditions)

    if link_capacity_objects:
        link_capacity_object = link_capacity_objects[0]
        answer = test_db_layout.MaaSLinkCapacityData.construct_maas_single_link_capacity_answer(link_capacity_object.link_id, link_capacity_object.capacity)

    err.log_error(err.INFO, "Sending 1 row of link capacity data")

    return answer


MAAS = None


def shutdown(sig_num, sf):
    MAAS.close()
    sys.exit(0)


def main():
    global MAAS
    MAAS = TestSupplier("Test MaaS", config.TEST_MAAS_DB)
    signal.signal(signal.SIGINT, shutdown)

    if MAAS.start():
        err.log_error(err.INFO, "Server started succesfully. Going to work!")
        MAAS.go_to_work()
    else:
        err.log_error(err.CRITICAL, "Could not start server succesfully. Aborting...")
        shutdown(1, None)

if __name__ == "__main__":
    if support.everything_installed():
        main()

