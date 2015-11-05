import signal
import sys
import time

from mobaas.socket_connections import client_connections
from mobaas.socket_connections import server_connections

from mobaas.database_connections import db_connections
from mobaas.database_connections import db_layout

from mobaas.mobaas_protocol import mobaas_protocol
from mobaas.mobaas_protocol import message_objects

from mobaas.frontend_support import handle_messages
from mobaas.frontend_support import pending_requests

from mobaas.common import error_logging as err
from mobaas.common import support

from mobaas import config as central_config

'''
Main class of MOBaaS.
Setups everything from database connections to socket connections and server ports
'''
class Frontend:
    def __init__(self):
        self.server = server_connections.Server("MOBaaS Consumer Connections Server", central_config.SERVER_PORT, central_config.SERVER_HOSTNAME)
        self.client = client_connections.Client("MOBaaS Supplier Connections Client")
        self.dbcc = db_connections.DBConnectionCollection("MOBaaS Databases")
        self.dbcc.create_multiple_connections(db_layout.DATABASE_NAMES)
        self.received_supplier_messages = False
        self.pending_request_queue = pending_requests.PendingRequestQueue()

    '''
    Start all underlying services
    '''
    def start(self):
        return (Frontend._start_x_with_y(self.dbcc, db_connections.DBConnectionCollection.start_all_connections)
               and Frontend._start_x_with_y(self.client, lambda x: client_connections.Client.create_connection(x, central_config.MaaS_hostname, central_config.MaaS_port))
               and Frontend._start_x_with_y(self.server, server_connections.Server.start)
               )

    '''
    Start a service x with a supplied function y
    If it fails, record it into the error log
    '''
    @staticmethod
    def _start_x_with_y(x, y):
        x_started = y(x)

        if x_started:
            err.log_error(err.INFO, str(x) + " has been started")
        else:
            err.log_error(err.CRITICAL, str(x) + " could not be started!")

        return x_started

    '''
    Sets the Frontend to work
    Goes through all phases of the underlying services to handle all messages
    '''
    def go_to_work(self):
        while True:
            self.server.accept_connections()
            self._handle_x_read_phase_with_y(self.client, handle_messages.handle_incoming_message_supplier)
            self._handle_x_read_phase_with_y(self.server, handle_messages.handle_incoming_message_consumer)
            Frontend._handle_x_send_phase(self.client)
            Frontend._handle_x_send_phase(self.server)
            Frontend._handle_x_destroy_unusable_connections_phase(self.client)
            Frontend._handle_x_destroy_unusable_connections_phase(self.server)
            self._handle_pending_requests()
            time.sleep(0.1)

    '''
    Handles the read phase of an underlying socket service x with function y
    Handles all messages with the protocol functions
    '''
    def _handle_x_read_phase_with_y(self, x, y):
        x.read_from_connections()
        connections = x.check_for_messages(mobaas_protocol.contains_complete_message)

        for connection in connections:
            messages = connection.consume_all_complete_messages(mobaas_protocol.contains_complete_message, mobaas_protocol.first_complete_message_ends_at)
            messages = map(mobaas_protocol.parse_message, messages)
            for message in messages:
                y(self, connection, message)

    '''
    Handles the send phase of an underlying socket service x
    '''
    @staticmethod
    def _handle_x_send_phase(x):
        x.send_to_connections()

    '''
    Handles destroying all unusable connections within the underlying socket service x
    '''
    @staticmethod
    def _handle_x_destroy_unusable_connections_phase(x):
        x.destroy_all_unusable_connections()

    '''
    Handle any pending requests if any are ready to be handled now
    '''
    def _handle_pending_requests(self):
        pending_requests = self.pending_request_queue.get_ready_to_be_handled_requests()

        for pending_request in pending_requests:
            connection = pending_request.connection
            request = pending_request.request_message
            err.log_error(err.INFO, "Pending request now possible. Rehandling request: " + str(request))
            handle_messages.handle_incoming_message_consumer(self, connection, request)

    '''
    Queue message, received on the connection, into the pending queue waiting on the missing_resource
    '''
    def queue_as_pending_request(self, connection, request_message, missing_resource):
        err.log_error(err.INFO, "Putting request {" + str(request_message) + "} in the pending queue. Waiting on " + str(missing_resource))
        self.pending_request_queue.add_pending_request(connection, request_message, missing_resource)

    '''
    Update all pending requests with the supplied_resource. Marking all the corresponding missing resourcess
    '''
    def process_supplied_resource(self, supplied_resource):
        self.pending_request_queue.process_supplied_resource(supplied_resource)

    '''
    Sends a message to the suppliers of this Frontend
    '''
    def ask_at_supplier(self, message):
        self.client.broadcast(message)

    '''
    Closes all underlying services of this Frontend
    '''
    def close(self):
        close_message = message_objects.EndConversation("MOBaaS is being closed")
        self.server.broadcast_close(close_message)
        self.client.broadcast_close(close_message)
        return self.dbcc.close_all_connections() and self.server.close() and self.client.close_all_connections()




'''
The one and only frontend instance of this MOBaaS machine
'''
FRONTEND = None

'''
Shutdown MOBaaS on the incoming signal
'''
def shutdown(sig_num, sf):
    FRONTEND.close()
    sys.exit(0)


'''
Main function to be called to start everything
Also signs up the shutdown function to the CTRL+C signal
'''
def main():
    global FRONTEND
    FRONTEND = Frontend()
    signal.signal(signal.SIGINT, shutdown)

    if FRONTEND.start():
        err.log_error(err.INFO, "Server started succesfully. Going to work!")
        FRONTEND.go_to_work()
    else:
        err.log_error(err.CRITICAL, "Could not start server succesfully. Aborting...")
        shutdown(1, None)

'''
Only call main if this module is called directly
'''
if __name__ == "__main__":
    if support.everything_installed():
        main()
