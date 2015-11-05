import socket
import select

from mobaas.common import error_logging as err
from mobaas.socket_connections import socket_connections

'''
Inherits from a socket connection collection and adds specific server
functionality
'''
class Server(socket_connections.SocketConnectionCollection):
    def __init__(self, name, port, hostname):
        socket_connections.SocketConnectionCollection.__init__(self, name)
        self.address = (hostname,port)
        self.sock = None
        self.connections = []
        self.returned_ids = []

    # Phase functions
    def start(self):
        result = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            s.bind(self.address)
            s.listen(5)
        except socket.error as e:
            err.log_error(err.CRITICAL, "Error during binding and listening to server socket '" + \
                              "'. Error " + str(e.errno) + ": " + str(e.strerror))
            s = None

        if not s:
            err.log_error(err.ERROR, "Shutting down server")
            result = False
        else:
            self.sock = s

        return result

    def accept_connections(self):
        while self.has_pending_connections():
            sock, address = self.sock.accept()
            connection_id = self.next_connection_id()

            connection_obj = socket_connections.SocketConnection(connection_id, sock, address, self)
            err.log_error(err.INFO, "A connection has been accepted " + str(connection_obj))

    def close(self):
        result = True
        err.log_error(err.INFO, "The " + self.name + " server is being stopped")
        if self.sock:
            result = self.close_all_connections()
            err.log_error(err.INFO, "Closing server socket")
            try:
                self.sock.close()
                result = result and True
            except socket.error as e:
                err.log_error(err.ERROR, "Could not cleanly close socket. Error " + str(e.errno) + ": " + str(e.strerror))
            err.log_error(err.INFO, "Server socket is closed")
        else:
            err.log_error(err.ERROR, "Tried to close the server, but the server was never correctly started!")

        return result

    # Support functions
    def has_pending_connections(self):
        readable, writable, exceptionable = select.select([self.sock], [], [], 0)

        return readable