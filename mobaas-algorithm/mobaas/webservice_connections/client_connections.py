import socket

from mobaas.common import error_logging as err
from mobaas.socket_connections import socket_connections

'''
Socket Client. Inherits from socket collection and adds
client specific functionality
'''
class Client(socket_connections.SocketConnectionCollection):
    def __init__(self, name):
        socket_connections.SocketConnectionCollection.__init__(self, name)

    def create_connection(self, hostname, port):
        result = True
        cid = self.next_connection_id()
        address = (hostname, port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.connect(address)
        except socket.error as e:
            err.log_error(err.ERROR, "Could not connect to " + hostname + ":" + str(port) + " because: " + str(e.errno) + " " + str(e.strerror))
            result = False
        else:
            connection = socket_connections.SocketConnection(cid, sock, address, self)
            err.log_error(err.INFO, "A connection has been made: " + str(connection))

        return result