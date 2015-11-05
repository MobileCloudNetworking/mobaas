from mobaas.common import config as common_config
from mobaas.common import support

from mobaas.database_connections import db_objects
from mobaas.database_connections import db_connections as dc

from mobaas.mobaas_protocol import data_objects as do


'''
Layout of the MOBaaS database structure
It is pretty much self explanatory if you know
the database structure already.
The database structure follows directly from the
mobaas protocol.
'''

MOBILITY_PREDICTED_DATABASE = "mobility_predicted_database"
MOB_PRED_TABLE = "mob_pred"

BANDWIDTH_PREDICTED_DATABASE = "bandwidth_predicted_database"
BAND_PRED_TABLE = "band_pred"

MP_FETCHED_DATABASE = "mp_fetched_database"
MP_FETCH_TABLE = "mp_fetch"

BP_FETCHED_DATABASE = "bp_fetched_database"
BP_FETCH_TABLE = "bp_fetch"
LINK_CAPACITY_TABLE = "link_capacity"

MEAN_DATA_DATABASE = "mean_data_database"
USER_INFORMATION_TABLE = "user_mobility_information"
FLOW_DATA_TABLE = "flow_data"


DATABASE_NAMES = [ MOBILITY_PREDICTED_DATABASE
                 , BANDWIDTH_PREDICTED_DATABASE
                 , MP_FETCHED_DATABASE
                 , BP_FETCHED_DATABASE
                 , MEAN_DATA_DATABASE
                 ]


class MobilityPredicted(db_objects.DBObject):
    database_name = MOBILITY_PREDICTED_DATABASE
    table_name = MOB_PRED_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("user_id", dc.DB_Int)
             , ("future_time", dc.DB_Text)
             , ("future_date", dc.DB_Text)
             , ("cell_id", dc.DB_Int)
             , ("probability", dc.DB_Int)
             ]


class BandwidthPredicted(db_objects.DBObject):
    database_name = BANDWIDTH_PREDICTED_DATABASE
    table_name = BAND_PRED_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("link_id", dc.DB_Int)
             , ("future_time", dc.DB_Time)
             , ("future_date", dc.DB_Date)
             , ("unused_capacity_prediction", dc.DB_Int)
             ]


class MPFetched(db_objects.DBObject):
    database_name = MP_FETCHED_DATABASE
    table_name = MP_FETCH_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("user_id", dc.DB_Int)
             , ("minute_of_day", dc.DB_Int)
             , ("date", dc.DB_Date)
             , ("day", dc.DB_Text)
             , ("cell_id", dc.DB_Int)
             ]


class BPFetched(db_objects.DBObject):
    database_name = BP_FETCHED_DATABASE
    table_name = BP_FETCH_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("link_id", dc.DB_Int)
             , ("time", dc.DB_Unix_Timestamp)
             , ("throughput_bps", dc.DB_Double)
             ]

    def to_tuple_without_link_id(self):
        return (self.time, self.throughput_bps)


class UserMobilityInformation(db_objects.DBObject):
    database_name = MEAN_DATA_DATABASE
    table_name = USER_INFORMATION_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("user_id", dc.DB_Int)
             , ("time", dc.DB_Time)
             , ("date", dc.DB_Date)
             , ("cell_id", dc.DB_Int)
             ]

    '''
    Takes first one that fits in a time resolution slot from the list
    Respects order
    '''
    @staticmethod
    def reduce_to_time_resolution(list_of_user_info, time_resolution):
        grouped_by_dates_orddict = support.group_by(list_of_user_info, lambda x: x.date)
        result = []

        for _, grouped_by_date in grouped_by_dates_orddict.items():
            time_grid_day = support.to_grid(grouped_by_date, time_resolution, lambda x: support.time_total_seconds(x.time), 0, common_config.SECONDS_IN_A_DAY)
            support.remove_none_from_list(time_grid_day)
            result = result + time_grid_day

        return result

    def to_protocol_movement_object(self):
        return do.Movement(self.time, self.date, self.cell_id)


class FlowData(db_objects.DBObject):
    database_name = MEAN_DATA_DATABASE
    table_name = FLOW_DATA_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("link_id", dc.DB_Int)
             , ("start_time", dc.DB_Unix_Timestamp_With_MSec)
             , ("stop_time", dc.DB_Unix_Timestamp_With_MSec)
             , ("source_ip", dc.DB_Text)
             , ("destination_ip", dc.DB_Text)
             , ("num_of_packets", dc.DB_Double)
             , ("num_of_bytes", dc.DB_Double)
             ]

    def to_protocol_flow_data(self):
        return do.FlowData(*self.to_tuple_without_link_id())

    def to_tuple_without_link_id(self):
        return (self.start_time, self.stop_time, self.source_ip, self.destination_ip, self.num_of_packets, self.num_of_bytes)


class LinkCapacityData(db_objects.DBObject):
    database_name = BP_FETCHED_DATABASE
    table_name = LINK_CAPACITY_TABLE
    layout = db_objects.DBObject.layout + \
             [ ("link_id", dc.DB_Int)
             , ("capacity", dc.DB_Int)
             ]