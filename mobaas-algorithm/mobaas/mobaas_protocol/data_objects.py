from mobaas.mobaas_protocol import protocol_types as pt


'''
Some of the message_objects contain information rows of information.
Each row of information is mapped to one of the data objects
below
'''

'''
Corresponds with a MP single user answer
'''
class Prediction(pt.ProtocolDictType):
    expected_keys_types = [ ("cell_id", pt.ProtocolInt)
                          , ("probability", pt.ProtocolFloat)
                          ]

    def __init__(self, cell_id, probability):
        pt.ProtocolDictType.__init__(self)
        self.cell_id = cell_id
        self.probability = probability

'''
Corresponds with a MP multi user answer
'''
class MultiUserPrediction(pt.ProtocolDictType):
    expected_keys_types = [ ("user_id", pt.ProtocolInt)
						  , ("current_cell_id", pt.ProtocolInt)
						  , ("next_time", pt.ProtocolString)
                          , ("probabilities", pt.ProtocolListType(Prediction))
                          ]

    def __init__(self, user_id, cell_id, next_time, probabilities):
        pt.ProtocolDictType.__init__(self)
        self.user_id = user_id
        self.current_cell_id = cell_id
        self.next_time = next_time
        self.probabilities = probabilities



'''
Corresponds with a MP single user MaaS answer
'''
class Movement(pt.ProtocolDictType):
    expected_keys_types = [ ("time", pt.ProtocolTime)
                          , ("date", pt.ProtocolDate)
                          , ("cell_id", pt.ProtocolInt)
                          ]

    def __init__(self, time, date, cell_id):
        pt.ProtocolDictType.__init__(self)
        self.time = time
        self.date = date
        self.cell_id = cell_id


'''
Corresponds with a BP single link flow data MaaS answer
'''
class FlowData(pt.ProtocolDictType):
    expected_keys_types = [ ("start_time", pt.ProtocolInt)
                          , ("stop_time", pt.ProtocolInt)
                          , ("source_ip", pt.ProtocolString)
                          , ("destination_ip", pt.ProtocolString)
                          , ("num_of_packets", pt.ProtocolFloat)
                          , ("num_of_bytes", pt.ProtocolFloat)
                          ]

    def __init__(self, start_time, stop_time, source_ip, destination_ip, num_of_packets, num_of_bytes):
        pt.ProtocolDictType.__init__(self)
        self.start_time = start_time
        self.stop_time = stop_time
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.num_of_packets = num_of_packets
        self.num_of_bytes = num_of_bytes
