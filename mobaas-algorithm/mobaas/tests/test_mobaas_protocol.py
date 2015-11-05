import datetime

from mobaas.mobaas_protocol import mobaas_protocol
from mobaas.mobaas_protocol import message_objects
from mobaas.mobaas_protocol import data_objects

from mobaas.tests import run_tests

ORDER = [ "test_parse_message"
        , "test_to_string"
        , "test_first_complete_message_ends_at"
        , "test_contains_complete_message"
        ]

MPREQUEST = "GET {\"type\": \"request-mp-single-user\", \"user_id\": 20, \"current_time\": \"12:23:45\", \"current_date\": \"2004-07-16\", \"future_time_delta\": 360, \"current_cell_id\": 17}\n\n"
MPANSWER = "RESULT {\"type\": \"answer-mp-single-user\", \"user_id\": 20, \"future_time\": \"12:29:45\", \"future_date\": \"2004-07-16\", \"predictions\": [{\"cell_id\": 45, \"probability\": 0.5}, {\"cell_id\": 65, \"probability\": 0.3}, {\"cell_id\": 128, \"probability\": 0.2}]}\n\n"
BPREQUEST = "GET {\"type\": \"request-bp-single-link\", \"link_id\": 20, \"current_time\": \"12:23:45\", \"current_date\": \"2004-07-16\", \"future_time_delta\": 1800}\n\n"
BPANSWER = "RESULT {\"type\": \"answer-bp-single-link\", \"link_id\": 20, \"future_time\": \"12:53:45\", \"future_date\": \"2004-07-16\", \"unused_capacity_prediction\": 45000000}\n\n"
MAASUSERREQUEST = "GET {\"type\": \"request-single-user-mobility-data\", \"user_id\": 20, \"start_time\": \"12:23:45\", \"start_date\": \"2004-07-16\", \"time_span\": 3600, \"time_resolution\": 60}\n\n"
MAASUSERANSWER = "RESULT {\"type\": \"answer-single-user-mobility-data\", \"user_id\": 20, \"start_date\": \"2005-06-28\", \"start_time\": \"14:56:16\", \"time_span\": 120, \"user_information\": [{\"time\": \"14:56:16\", \"date\": \"2005-06-28\", \"cell_id\": 45}, {\"time\": \"14:57:16\", \"date\": \"2005-06-28\", \"cell_id\": 45}, {\"time\": \"14:58:16\", \"date\": \"2005-06-28\", \"cell_id\": 46}]}\n\n"

MAASLINKREQUEST = "GET {\"type\": \"request-single-link-flow-data\", \"link_id\": 20, \"start_date\": \"2004-07-16\", \"start_time\": \"12:23:45\", \"time_span\": 3600}\n\n"
MAASLINKANSWER = "RESULT {\"type\": \"answer-single-link-flow-data\", \"link_id\": 20, \"flow_data\": [{\"start_time\": 1089980325, \"stop_time\": 1089983625, \"source_ip\": \"130.106.49.46\", \"destination_ip\": \"84.56.78.405\", \"num_of_packets\": 10394856, \"num_of_bytes\": 103948560}, {\"start_time\": 1089970625, \"stop_time\": 1089990625, \"source_ip\": \"129.106.50.45\", \"destination_ip\": \"84.56.78.405\", \"num_of_packets\": 10394853, \"num_of_bytes\": 103948559}]}\n\n"
MAASLINKCAPREQUEST = "GET {\"type\": \"request-single-link-capacity\", \"link_id\": 20}\n\n"
MAASLINKCAPANSWER = "RESULT {\"type\": \"answer-single-link-capacity\", \"link_id\": 20, \"capacity\": 300000000}\n\n"
ERROR = "ERROR {\"error_code\": 102, \"error_message\": \"The historical information needs to be retrieved from MaaS. Calculating will take longer than expected.\"}\n\n"
ENDCONVERSATION = "ENDCONVERSATION {\"reason\": \"I have gotten all the predictions that I needed\"}\n\n"

MPREQUEST_OBJ = message_objects.MPSingleUserRequest( user_id=20
                                                   , current_time=datetime.time(hour=12, minute=23, second=45)
                                                   , current_date=datetime.date(year=2004, month=07, day=16)
                                                   , future_time_delta=360
                                                   , current_cell_id=17
                                                   )

MPANSWER_OBJ = message_objects.MPSingleUserAnswer( user_id=20
                                                 , future_time=datetime.time(hour=12, minute=29, second=45)
                                                 , future_date=datetime.date(year=2004, month=07, day=16)
                                                 , predictions=[ data_objects.Prediction(45, 0.50)
                                                               , data_objects.Prediction(65, 0.30)
                                                               , data_objects.Prediction(128, 0.20)
                                                               ]
                                                 )

BPREQUEST_OBJ = message_objects.BPSingleLinkRequest( link_id=20
                                                   , current_time=datetime.time(hour=12, minute=23, second=45)
                                                   , current_date=datetime.date(year=2004, month=07, day=16)
                                                   , future_time_delta=1800
                                                   )

BPANSWER_OBJ = message_objects.BPSingleLinkAnswer( link_id=20
                                                 , future_time=datetime.time(hour=12, minute=53, second=45)
                                                 , future_date=datetime.date(year=2004, month=07, day=16)
                                                 , unused_capacity_prediction=45000000
                                                 )

MAASUSERREQUEST_OBJ = message_objects.MaaSSingleUserDataRequest( user_id=20
                                                               , start_time=datetime.time(hour=12, minute=23, second=45)
                                                               , start_date=datetime.date(year=2004, month=07, day=16)
                                                               , time_span=3600
                                                               , time_resolution=60
                                                               )

MAASUSERANSWER_OBJ = message_objects.MaaSSingleUserDataAnswer( user_id=20
                                                             , start_date=datetime.date(year=2005, month=6, day=28)
                                                             , start_time=datetime.time(hour=14, minute=56, second=16)
                                                             , time_span=120
                                                             , user_information=[ data_objects.Movement(datetime.time(14, 56, 16), datetime.date(2005, 06, 28), 45)
                                                                                , data_objects.Movement(datetime.time(14, 57, 16), datetime.date(2005, 06, 28), 45)
                                                                                , data_objects.Movement(datetime.time(14, 58, 16), datetime.date(2005, 06, 28), 46)
                                                                                ]
                                                             )

MAASLINKREQUEST_OBJ = message_objects.MaaSSingleLinkDataRequest( link_id=20
                                                               , start_time=datetime.time(hour=12, minute=23, second=45)
                                                               , start_date=datetime.date(year=2004, month=07, day=16)
                                                               , time_span=3600
                                                               )

MAASLINKANSWER_OBJ = message_objects.MaaSSingleLinkDataAnswer( link_id=20
                                                             , flow_data=[ data_objects.FlowData(1089980325, 1089983625, "130.106.49.46", "84.56.78.405", 10394856, 103948560)
                                                                         , data_objects.FlowData(1089970625, 1089990625, "129.106.50.45", "84.56.78.405", 10394853, 103948559)
                                                                         ]
                                                             )

MAASLINKCAPREQUEST_OBJ = message_objects.MaaSSingleLinkCapacityRequest( link_id=20
                                                                      )

MAASLINKCAPANSWER_OBJ = message_objects.MaaSSingleLinkCapacityAnswer( link_id=20
                                                                    , capacity=300000000
                                                                    )

ERROR_OBJ = message_objects.Error( error_code=102
                                 , error_message="The historical information needs to be retrieved from MaaS. Calculating will take longer than expected."
                                 )

ENDCONVERSATION_OBJ = message_objects.EndConversation( reason="I have gotten all the predictions that I needed"
                                                     )

MESSAGES = [ (MPREQUEST, MPREQUEST_OBJ)
           , (MPANSWER, MPANSWER_OBJ)
           , (BPREQUEST, BPREQUEST_OBJ)
           , (BPANSWER, BPANSWER_OBJ)
           , (MAASUSERREQUEST, MAASUSERREQUEST_OBJ)
           , (MAASUSERANSWER, MAASUSERANSWER_OBJ)
           , (MAASLINKREQUEST, MAASLINKREQUEST_OBJ)
           , (MAASLINKANSWER, MAASLINKANSWER_OBJ)
           , (MAASLINKCAPREQUEST, MAASLINKCAPREQUEST_OBJ)
           , (MAASLINKCAPANSWER, MAASLINKCAPANSWER_OBJ)
           , (ERROR, ERROR_OBJ)
           , (ENDCONVERSATION, ENDCONVERSATION_OBJ)
           ]

def test_parse_message():
    [run_tests.compare_answer( mobaas_protocol.parse_message(msg_str)
                             , msg_obj
                             , "Check parse_message for " + msg_str
                             ) for msg_str, msg_obj in MESSAGES]

def test_contains_complete_message():
    [run_tests.compare_answer( mobaas_protocol.contains_complete_message(msg_str)
                             , True
                             , "Check contains_complete_message for " + msg_str
                             ) for msg_str, _ in MESSAGES]

def test_first_complete_message_ends_at():
    [run_tests.compare_answer( mobaas_protocol.first_complete_message_ends_at(msg_str)
                             , len(msg_str) - 1
                             , "Check first_complete_message_ends_at for " + msg_str
                             ) for msg_str, _ in MESSAGES]

def test_to_string():
    [run_tests.compare_answer( str(msg_obj)
                             , msg_str
                             , "Check __str__ for " + msg_str
                             ) for msg_str, msg_obj in MESSAGES]