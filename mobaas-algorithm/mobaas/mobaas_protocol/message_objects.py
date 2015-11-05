from mobaas.mobaas_protocol import protocol_types as pt
from mobaas.mobaas_protocol import data_objects as dobj

'''
Each of the classes below correspond with a message
in the protocol of MOBaaS. By inheriting the ProtocolDictType,
it is possible to automatically parse a message as a JSON dict
without adding any new functionality. In this regard, the messaging
system works more or less like the db_objects ORM for the database.
'''
class Message(pt.ProtocolDictType):
    prefix = ""
    expected_keys_types = []

    def __init__(self):
        pt.ProtocolDictType.__init__(self)

    def __str__(self):
        json_body = self.generate_json(self)

        return self.prefix + " " + json_body + '\n' + '\n'


class Request(Message):
    prefix = "GET"
    expected_keys_types = [("type", pt.ProtocolString)]
    type = ""

    def __init__(self):
        Message.__init__(self)

    @classmethod
    def get_expected_keys(cls):
        return [key for key, type in cls.expected_keys_types if key != "type"]

    @classmethod
    def get_expected_keys_types(cls):
        result = dict(cls.expected_keys_types)
        del result["type"]
        return result.items()


class Answer(Message):
    prefix = "RESULT"
    expected_keys_types = [("type", pt.ProtocolString)]
    type = ""

    def __init__(self):
        Message.__init__(self)

    @classmethod
    def get_expected_keys(cls):
        return [key for key, type in cls.expected_keys_types if key != "type"]

    @classmethod
    def get_expected_keys_types(cls):
        result = dict(cls.expected_keys_types)
        del result["type"]
        return result.items()


class Error(Message):
    prefix = "ERROR"
    expected_keys_types = Message.expected_keys_types + \
             [ ("error_code", pt.ProtocolInt)
             , ("error_message", pt.ProtocolString)
             ]

    def __init__(self, error_code, error_message):
        Message.__init__(self)
        self.error_code = error_code
        self.error_message = error_message


class EndConversation(Message):
    prefix = "ENDCONVERSATION"
    expected_keys_types = Message.expected_keys_types + \
             [("reason", pt.ProtocolString)]

    def __init__(self, reason):
        Message.__init__(self)
        self.reason = reason


class MPRelated:
    expected_keys_types = [("user_id", pt.ProtocolInt)]

    def __init__(self, user_id):
        self.user_id = user_id


class BPRelated:
    expected_keys_types = [("link_id", pt.ProtocolInt)]

    def __init__(self, link_id):
        self.link_id = link_id


class MPSingleUserRequest(Request, MPRelated):
    expected_keys_types = Request.expected_keys_types + MPRelated.expected_keys_types + \
                          [ ("current_time", pt.ProtocolTime)
                          , ("current_date", pt.ProtocolDate)
                          , ("future_time_delta", pt.ProtocolInt)
                          , ("current_cell_id", pt.ProtocolInt)
                          ]
    type = "request-mp-single-user"

    def __init__(self, user_id, current_time, current_date, future_time_delta, current_cell_id):
        Request.__init__(self)
        MPRelated.__init__(self, user_id)
        self.current_time = current_time
        self.current_date = current_date
        self.future_time_delta = future_time_delta
        self.current_cell_id = current_cell_id


class MPMultiUserRequest(Request, MPRelated):
    expected_keys_types = Request.expected_keys_types + MPRelated.expected_keys_types + \
                          [ ("current_time", pt.ProtocolString)
                          , ("current_date", pt.ProtocolString)
                          , ("future_time_delta", pt.ProtocolInt)
                          ]
    type = "request-mp-multi-user"

    def __init__(self, user_id, current_time, current_date, future_time_delta):
        Request.__init__(self)
        MPRelated.__init__(self, user_id)
        self.current_time = current_time
        self.current_date = current_date
        self.future_time_delta = future_time_delta




class MaaSSingleUserDataRequest(Request, MPRelated):
    expected_keys_types = Request.expected_keys_types + MPRelated.expected_keys_types + \
                          [ ("start_time", pt.ProtocolTime)
                          , ("start_date", pt.ProtocolDate)
                          , ("time_span", pt.ProtocolInt)
                          , ("time_resolution", pt.ProtocolInt)
                          ]
    type = "request-single-user-mobility-data"

    def __init__(self, user_id, start_time, start_date, time_span, time_resolution):
        Request.__init__(self)
        MPRelated.__init__(self, user_id)
        self.start_time = start_time
        self.start_date = start_date
        self.time_span = time_span
        self.time_resolution = time_resolution


class BPSingleLinkRequest(Request, BPRelated):
    expected_keys_types = Request.expected_keys_types + BPRelated.expected_keys_types + \
                          [ ("current_time", pt.ProtocolTime)
                          , ("current_date", pt.ProtocolDate)
                          , ("future_time_delta", pt.ProtocolInt)
                          ]
    type = "request-bp-single-link"

    def __init__(self, link_id, current_time, current_date, future_time_delta):
        Request.__init__(self)
        BPRelated.__init__(self, link_id)
        self.current_time = current_time
        self.current_date = current_date
        self.future_time_delta = future_time_delta


class MaaSSingleLinkDataRequest(Request, BPRelated):
    expected_keys_types = Request.expected_keys_types + BPRelated.expected_keys_types + \
                          [ ("start_date", pt.ProtocolDate)
                          , ("start_time", pt.ProtocolTime)
                          , ("time_span", pt.ProtocolInt)
                          ]
    type = "request-single-link-flow-data"

    def __init__(self, link_id, start_date, start_time, time_span):
        Request.__init__(self)
        BPRelated.__init__(self, link_id)
        self.start_time = start_time
        self.start_date = start_date
        self.time_span = time_span


class MaaSSingleLinkCapacityRequest(Request, BPRelated):
    expected_keys_types = Request.expected_keys_types + BPRelated.expected_keys_types + \
                          [
                          ]
    type = "request-single-link-capacity"

    def __init__(self, link_id):
        Request.__init__(self)
        BPRelated.__init__(self, link_id)


class MPSingleUserAnswer(Answer, MPRelated):
    expected_keys_types = Answer.expected_keys_types + MPRelated.expected_keys_types + \
                          [ ("future_time", pt.ProtocolTime)
                          , ("future_date", pt.ProtocolDate)
                          , ("predictions", pt.ProtocolListType(dobj.Prediction))
                          ]
    type = "answer-mp-single-user"

    def __init__(self, user_id, future_time, future_date, predictions):
        Answer.__init__(self)
        MPRelated.__init__(self, user_id)
        self.future_time = future_time
        self.future_date = future_date
        self.predictions = predictions


class MPMultiUserAnswer(Answer):
    expected_keys_types = Answer.expected_keys_types + [("multi_user_predictions", pt.ProtocolListType(dobj.MultiUserPrediction))]
    type = "answer-mp-multi-user"

    def __init__(self, predictions):
        Answer.__init__(self)
        #MPRelated.__init__(self, user_id)
        self.multi_user_predictions = predictions


class MaaSSingleUserDataAnswer(Answer, MPRelated):
    expected_keys_types = Answer.expected_keys_types + MPRelated.expected_keys_types + \
                          [ ("start_date", pt.ProtocolDate)
                          , ("start_time", pt.ProtocolTime)
                          , ("time_span", pt.ProtocolInt)
                          , ("user_information", pt.ProtocolListType(dobj.Movement))
                          ]
    type = "answer-single-user-mobility-data"

    def __init__(self, user_id, start_date, start_time, time_span, user_information):
        Answer.__init__(self)
        MPRelated.__init__(self, user_id)
        self.start_date = start_date
        self.start_time = start_time
        self.time_span = time_span
        self.user_information = user_information


class BPSingleLinkAnswer(Answer, BPRelated):
    expected_keys_types = Answer.expected_keys_types + BPRelated.expected_keys_types + \
                          [ ("future_time", pt.ProtocolTime)
                          , ("future_date", pt.ProtocolDate)
                          , ("unused_capacity_prediction", pt.ProtocolFloat)
                          ]
    type = "answer-bp-single-link"

    def __init__(self, link_id, future_time, future_date, unused_capacity_prediction):
        Answer.__init__(self)
        BPRelated.__init__(self, link_id)
        self.future_time = future_time
        self.future_date = future_date
        self.unused_capacity_prediction = unused_capacity_prediction


class MaaSSingleLinkDataAnswer(Answer, BPRelated):
    expected_keys_types = Answer.expected_keys_types + BPRelated.expected_keys_types + \
                          [ ("flow_data", pt.ProtocolListType(dobj.FlowData))
                          ]
    type = "answer-single-link-flow-data"

    def __init__(self, link_id, flow_data):
        Answer.__init__(self)
        BPRelated.__init__(self, link_id)
        self.flow_data = flow_data


class MaaSSingleLinkCapacityAnswer(Answer, BPRelated):
    expected_keys_types = Answer.expected_keys_types + BPRelated.expected_keys_types + \
                          [ ("capacity", pt.ProtocolInt)
                          ]
    type = "answer-single-link-capacity"

    def __init__(self, link_id, capacity):
        Answer.__init__(self)
        BPRelated.__init__(self, link_id)
        self.capacity = capacity
