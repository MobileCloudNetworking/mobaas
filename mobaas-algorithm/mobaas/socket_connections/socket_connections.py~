import socket
import select
import datetime

from mobaas.common import error_logging as err
from mobaas.common import connection_collection

from mobaas.socket_connections import config

'''
A collection of socket connections with functionality
both found in clients and servers
'''
class SocketConnectionCollection(connection_collection.ConnectionCollection):
    def __init__(self, name):
        connection_collection.ConnectionCollection.__init__(self, name)

    def close_all_connections(self):
        result = True
        err.log_error(err.INFO, "All socket connections are being closed...")
        for connection in self.connections:
            result = result and connection.close()

        return result

    # Phases
    '''
    Empty all socket receive buffers and put the data in the connection buffers
    '''
    def read_from_connections(self):
        connections = self.waiting_for_read_connections()

        for connection in connections:
            connection.read_buffer()

        return connections

    '''
    Finds all connections that has received a complete message according to message_check_func
    '''
    def check_for_messages(self, message_check_func):
        return [connection for connection in self.connections if connection.received_complete_message(message_check_func)]

    '''
    Empties the connection send buffers into their socket send buffers
    '''
    def send_to_connections(self):
        connections = [connection for connection in self.can_send_connections() if connection.has_data_to_send()]

        for connection in connections:
            connection.send_buffer()

        return connections

    '''
    Destroys all connections that had to be closed or excepted
    '''
    def destroy_all_unusable_connections(self):
        unusable_connections = self.excepted_connections()

        for unusable_connection in unusable_connections:
            unusable_connection.close()

    # Support functions
    def get_all_connection_sockets(self):
        return [connection.sock for connection in self.connections]

    def waiting_for_read_connections(self):
        readable, writable, exceptionable = select.select(self.get_all_connection_sockets(), [], [], 0)

        return self.map_sockets_to_connections(readable)

    def can_send_connections(self):
        readable, writeable, exceptionable = select.select([], self.get_all_connection_sockets(), [], 0)

        return self.map_sockets_to_connections(writeable)

    def excepted_connections(self):
        readable, writeable, exceptionable = select.select([], [], self.get_all_connection_sockets(), 0)
        excepted_connections = self.map_sockets_to_connections(exceptionable)
        closed_off_connections = [connection for connection in self.connections if connection.needs_to_be_closed() and (not connection in excepted_connections)]

        return excepted_connections + closed_off_connections

    def map_sockets_to_connections(self, socks):
        return [connection for connection in self.connections for sock in socks if sock.fileno() == connection.sock.fileno()]

    def broadcast(self, message):
        connections = self.can_send_connections()

        for connection in connections:
            connection.add_message(message)

        if len(connections) == 0:
            err.log_error(err.ERROR, "Requested to broadcast a message to all connections but there are not connections in " + str(self))
            err.log_error(err.ERROR, "Message was: " + str(message))

    '''
    Broadcast a close message
    '''
    def broadcast_close(self, close_message):
        err.log_error(err.INFO, "Broadcasting close message: " + str(close_message))
        for connection in self.can_send_connections():
            connection.send_close(close_message)

'''
Class to represent a socket connection. Functionality is the same as the SocketConnectionCollection
but than for a single socket connection. Self explanatory really.
'''
class SocketConnection(connection_collection.Connection):
    def __init__(self, cid, sock, address, sock_connection_collection):
        connection_collection.Connection.__init__(self, cid, sock_connection_collection)
        self.sock = sock
        self.address = address
        self.read_message_buffer = ""
        self.send_message_buffer = ""
        self.needs_closing = False

        sock.setblocking(1)
        sock.settimeout(config.TIMEOUT)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, config.RCVBUF_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, config.SNDBUF_SIZE)

    def add_message(self, message):
        self.send_message_buffer += str(message)

    def can_send_data(self):
        readable, writeable, exceptionable = select.select([], [self.sock], [], 0)

        return len(writeable) > 0

    def has_data_to_send(self):
        return len(self.send_message_buffer) > 0

    def has_data_to_read(self):
        readable, writeable, exceptionable = select.select([self.sock], [], [], 0)
        result = len(readable) > 0

        if result:
            #Check if connection is closed or not if it has something to read
            try:
                peeked = self.sock.recv(64, socket.MSG_PEEK)
            except socket.error:
                self.needs_closing = True
                result = False
            else:
                if len(peeked) == 0:
                    self.needs_closing = True
                    result = False

        return result

    def read_buffer(self):
        while self.has_data_to_read():
            try:
                self.read_message_buffer += self.sock.recv(config.RECEIVE_CHUNK_SIZE)
            except socket.error as e:
                err.log_error(err.ERROR, "Tried to read from self " + str(self) + " but an error occured. Error " + str(e.errno) + ": " + str(e.strerror))
                break

    def send_buffer(self):
        while self.has_data_to_send():
            try:
                to_send = self.send_message_buffer[:config.SEND_CHUNK_SIZE]
                has_send = self.sock.send(to_send)
            except socket.error as e:
                err.log_error(err.ERROR, "Could not send data over the connection " + str(self) + ". Error " + str(e.errno) + ": " + str(e.strerror))
                break
            self.send_message_buffer = self.send_message_buffer[has_send:]

        if not self.can_send_data():
            self.needs_closing = True

    def received_complete_message(self, message_check_func):
        return message_check_func(self.read_message_buffer)

    def consume_complete_message(self, message_check_func):
        last_index = message_check_func(self.read_message_buffer)
        message = self.read_message_buffer[0:last_index + 1]
        self.read_message_buffer = self.read_message_buffer[last_index + 1:]

        return message

    def consume_all_complete_messages(self, has_message_func, index_message_func):
        result = []

        while has_message_func(self.read_message_buffer):
            result.append(self.consume_complete_message(index_message_func))

        return result

    def needs_to_be_closed(self):
        return self.needs_closing and len(self.read_message_buffer) == 0 and len(self.send_message_buffer) == 0

    def send_close(self, close_message):
        self.add_message(close_message)
        self.send_buffer()

    def close(self):
        result = False
        try:
            self.sock.close()
            result = True
        except socket.error:
            err.log_error(err.ERROR, "Tried to close a connection, but it seems something was wrong with the connection. Closed the connection anyway. Do not need to do anything about this.")

        self.connection_collection.remove_connection(self.cid)

        return result

    def __str__(self):
        return "[Connection id: " + str(self.cid) + " address: " + str(self.address) + " ]"
