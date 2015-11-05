from mobaas.common import error_logging as err


'''
Class to express a collection of connections
Used by the database connections, client connections
and server connections
'''
class ConnectionCollection:
    def __init__(self, name):
        self.name = name
        self.connections = []
        self.returned_ids = [] #stack of returned connection id's that can be reused

    # Bookkeeping functions
    def add_connection(self, connection):
        err.log_error(err.INFO, "Connection " + str(connection.cid) + " has been added to Connection_Collection " + self.name)
        self.connections.append(connection)

    def remove_connection(self, connection_id):
        if connection_id in self.all_connection_ids():
            self.returned_ids.append(connection_id)
            self.connections = [connection for connection in self.connections if not connection.cid == connection_id]

    def all_connection_ids(self):
        return [connection.cid for connection in self.connections]

    def next_connection_id(self):
        if self.returned_ids:
            result = self.returned_ids.pop(-1)
        else:
            connection_ids = self.all_connection_ids()

            if connection_ids:
                result = max(connection_ids) + 1
            else:
                result = 0

        return result

    def __str__(self):
        connections_ids_str = ", ".join(map(str, self.all_connection_ids()))

        return "[Connection_Collection " + self.name + " containing connections{" + connections_ids_str + "}]"

'''
Class to express a connection within the connection collection
'''
class Connection:
    def __init__(self, cid, connection_collection):
        self.cid = cid
        self.connection_collection = connection_collection

        connection_collection.add_connection(self)
