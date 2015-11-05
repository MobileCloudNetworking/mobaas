import datetime
import time

from mobaas.socket_connections import client_connections
from mobaas.mobaas_protocol import message_objects

from mobaas.mobaas_protocol import mobaas_protocol

from mobaas.common import error_logging as err
from mobaas.common import fifo
from mobaas import config

'''
A test consumer using a socket client as an underlying service
Cycles through a given list of messages and sends the first next
message every wait_between sends.
Most of the functions are self explanatory
'''
class TestConsumer:
    def __init__(self, name, test_messages, wait_between_sends):
        self.client = client_connections.Client(name)
        self.test_messages = fifo.FifoQueue(map(str, test_messages))
        self.wait_between_sends = wait_between_sends
        self.next_send_time = datetime.datetime.now()

    def start(self):
        #Start connection to MOBaaS server frontend
        connection_started = self.client.create_connection(config.SERVER_HOSTNAME, config.SERVER_PORT)

        if connection_started:
            err.log_error(err.INFO, "Started connection to MOBaaS frontend")
        else:
            err.log_error(err.CRITICAL, "Could not create a connection to MOBaaS frontend!")

        return connection_started

    def go_to_work(self):
        while True:
            self._handle_read_phase()
            self._handle_send_phase()
            self._handle_destroy_unusable_connections_phase()

            time.sleep(0.1)

    def _handle_read_phase(self):
        self.client.read_from_connections()
        connections = self.client.check_for_messages(mobaas_protocol.contains_complete_message)

        for connection in connections:
            messages = connection.consume_all_complete_messages(mobaas_protocol.contains_complete_message, mobaas_protocol.first_complete_message_ends_at)
            for message in messages:
                parsed_message = mobaas_protocol.parse_message(message)
                handle_message(connection, parsed_message)

    def _handle_send_phase(self):
        if self.time_to_send():
            self.set_next_time()
            next_message = self.pop_next_message()
            err.log_error(err.INFO, "Sending message: " + str(next_message))

            for connection in self.client.can_send_connections():
                connection.add_message(next_message)

        self.client.send_to_connections()

    def _handle_destroy_unusable_connections_phase(self):
        self.client.destroy_all_unusable_connections()

    def time_to_send(self):
        return (self.next_send_time - datetime.datetime.now()).total_seconds() <= 0

    def set_next_time(self):
        td = datetime.timedelta(seconds=self.wait_between_sends)
        self.next_send_time = self.next_send_time + td
        err.log_error(err.INFO, "Next send will be at: " + self.next_send_time.strftime("[%H:%M:%S %d-%m-%Y]"))

    def close(self):
        err.log_error(err.INFO, "Closing Test Consumer.")
        self.client.broadcast_close(message_objects.EndConversation("Client is being closed"))
        self.client.close_all_connections()
        err.log_error(err.INFO, "Closed the Test Consumer. Now Quitting.")

    def pop_next_message(self):
        next_message = self.test_messages.pop_first()
        self.test_messages.append(next_message)

        return next_message

    def __str__(self):
        return "TestConsumer " + self.client.name


def handle_message(connection, msg):
    if isinstance(msg, message_objects.EndConversation):
        err.log_error(err.INFO, "Connection " + str(connection) + " is requested to end because: " + msg.reason)
        connection.close()
    else:
        err.log_error(err.INFO, "Received message: " + str(msg))
