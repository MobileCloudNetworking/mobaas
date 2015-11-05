import datetime

from mobaas.common import support

from mobaas.database_connections import db_layout
from mobaas.database_connections import db_connections

from mobaas.tests import run_tests

ORDER = [ "test_user_info_group_by_date"
        , "test_user_info_reduce_to_time_resolution"
        ]

def setup_user_info(user_id, hour, minute, second, year, month, day, cell_id):
    return db_layout.UserMobilityInformation.new( db_connections.DBConnectionCollection("Test")
                                                , user_id
                                                , datetime.time(hour=hour, minute=minute, second=second)
                                                , datetime.date(year=year, month=month, day=day)
                                                , cell_id
                                                )


def setup_user_info_list(user_info_list):
    result = []
    for user_info in user_info_list:
        result.append(setup_user_info(*user_info))
    return result

USER_INFO_1_ARGS = [1, 14, 23, 01, 1991, 10, 17, 1004]
USER_INFO_2_ARGS = [1, 14, 23, 11, 1991, 10, 17, 1004]
USER_INFO_3_ARGS = [1, 14, 23, 21, 1991, 10, 18, 1004]
USER_INFO_4_ARGS = [1, 14, 23, 31, 1991, 10, 18, 1003]
USER_INFO_5_ARGS = [1, 14, 24, 01, 1991, 10, 19, 1005]
USER_INFO_6_ARTS = [1, 14, 23, 12, 1991, 10, 17, 1004]

USER_INFO_ARGS_LIST = [ USER_INFO_3_ARGS
                      , USER_INFO_1_ARGS
                      , USER_INFO_5_ARGS
                      , USER_INFO_4_ARGS
                      , USER_INFO_2_ARGS
                      , USER_INFO_6_ARTS
                      ]

USER_INFO_1_ARGS_2 = [1, 14, 23, 01, 1991, 10, 17, 1004]
USER_INFO_2_ARGS_2 = [1, 14, 23, 11, 1991, 10, 17, 1004]
USER_INFO_3_ARGS_2 = [1, 14, 23, 21, 1991, 10, 17, 1004]
USER_INFO_4_ARGS_2 = [1, 14, 23, 31, 1991, 10, 17, 1003]
USER_INFO_5_ARGS_2 = [1, 14, 24, 01, 1991, 10, 17, 1005]

USER_INFO_ARGS_LIST_2 = [ USER_INFO_3_ARGS_2
                        , USER_INFO_1_ARGS_2
                        , USER_INFO_5_ARGS_2
                        , USER_INFO_4_ARGS_2
                        , USER_INFO_2_ARGS_2
                        ]

def _set_different(list1, list2):
    return [item1 for item1 in list1 if not (item1 in list2)]

def test_user_info_reduce_to_time_resolution():
    user_infos = setup_user_info_list(USER_INFO_ARGS_LIST_2)

    result_1 = db_layout.UserMobilityInformation.reduce_to_time_resolution(user_infos, 1)
    answer_1 = user_infos
    run_tests.compare_answer(len(_set_different(result_1, answer_1)), 0, "reduce_time_resolution with 1 second")

    result_10 = db_layout.UserMobilityInformation.reduce_to_time_resolution(user_infos, 10)
    answer_10 = user_infos
    run_tests.compare_answer(len(_set_different(result_10, answer_10)), 0, "reduce_time_resolution with 10 seconds")

    result_20 = db_layout.UserMobilityInformation.reduce_to_time_resolution(user_infos, 20)
    answer_20 = setup_user_info_list([USER_INFO_1_ARGS_2, USER_INFO_3_ARGS_2, USER_INFO_5_ARGS_2])
    run_tests.compare_answer(len(_set_different(result_20, answer_20)), 0, "reduce_time_resolution with 20 seconds")

    result_60 = db_layout.UserMobilityInformation.reduce_to_time_resolution(user_infos, 60)
    answer_60 = setup_user_info_list([USER_INFO_3_ARGS_2, USER_INFO_5_ARGS_2])
    run_tests.compare_answer(len(_set_different(result_60, answer_60)), 0, "reduce_time_resolution with 60 seconds")


