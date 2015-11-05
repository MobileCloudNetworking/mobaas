from mobaas.database_connections import db_connections
from mobaas.database_connections import db_layout

from mobaas.demo_programmes import config

from mobaas.mobaas_protocol import message_objects

'''
Database structure used by the Test supplier
'''
class MaaSUserMobilityInformation(db_layout.UserMobilityInformation):
    database_name = config.TEST_MAAS_DB
    table_name = config.TEST_MAAS_USER_INFO_TABLE

    def __hash__(self):
        return self.oid

    @staticmethod
    def construct_maas_single_user_data_answer(user_id, start_date, start_time, time_span, list_user_information):
        protocol_movements = map(lambda x: x.to_protocol_movement_object(), list_user_information)

        return message_objects.MaaSSingleUserDataAnswer(user_id, start_date, start_time, time_span, protocol_movements)


class MaaSFlowData(db_layout.FlowData):
    database_name = config.TEST_MAAS_DB
    table_name = config.TEST_MAAS_FLOW_DATA_TABLE

    @staticmethod
    def construct_maas_single_link_answer(link_id, list_db_flow_data):
        protocol_flow_data = map(lambda x: x.to_protocol_flow_data(), list_db_flow_data)
        return message_objects.MaaSSingleLinkDataAnswer(link_id, protocol_flow_data)

    '''
    Specialized way to retrieve flow data. Query could not fit within the given ORM structure
    so a specialized function has been created.
    '''
    @classmethod
    def retrieve_flow_data(cls, dbcc, link_id, start_time, stop_time):
        con = dbcc.retrieve_connection(cls.database_name)
        layout_dict = dict(cls.layout)

        select = "*"
        table = cls.table_name
        link_id_sql = layout_dict["link_id"].format_to_db_value(link_id)
        start_time_sql = layout_dict["start_time"].format_to_db_value(start_time)
        stop_time_sql = layout_dict["stop_time"].format_to_db_value(stop_time)

        where_query = ("WHERE link_id = " + link_id_sql + " AND "
                       "("
                        "(" + start_time_sql + " <= start_time AND " + stop_time_sql + " >= stop_time)"
                        "OR (" + start_time_sql + " >= start_time AND " + start_time_sql + " <= stop_time)"
                        "OR (" + stop_time_sql + " >= start_time AND " + stop_time_sql + " <= stop_time)"
                       ")"
                      )

        mysql_rows = con.retrieve(select, table, where_query)

        result = []

        for mysql_row in mysql_rows:
            result.append(cls.object_from_mysql_row(dbcc, mysql_row))

        return result

class MaaSLinkCapacityData(db_layout.LinkCapacityData):
    database_name = config.TEST_MAAS_DB
    table_name = config.TEST_MAAS_LINK_CAPACITY_DATA_TABLE

    @staticmethod
    def construct_maas_single_link_capacity_answer(link_id, capacity):
        return message_objects.MaaSSingleLinkCapacityAnswer(link_id, capacity)
