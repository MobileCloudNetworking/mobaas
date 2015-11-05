import datetime

from mobaas.common import support

'''
A supplied resource is made when a clear data function
has found data that has been supplied by MaaS. The resource
contains information about the data that has been supplied
and can be used on a missing resource to update its missing data
ranges.

Each supplied resource contains a function to convert a mobaas_protocol.message_objects
to a supplied resource.
'''
class SuppliedResource():
    def __init__(self, supplied):
        self.supplied = supplied

    def to_supplied_info(self):
        return self.supplied

    def __str__(self):
        return str(self.supplied)

    def __repr__(self):
        return str(self)


class SuppliedUserInfo(SuppliedResource):
    def __init__(self, supplied_date_time_range):
        SuppliedResource.__init__(self, supplied_date_time_range)

    @staticmethod
    def from_maas_user_info_message_to_supplied_info(msg):
        supplied_resource = None

        if msg.time_span > 0:
            start_date_time = datetime.datetime.combine(msg.start_date, msg.start_time)
            end_date_time = start_date_time + datetime.timedelta(seconds=msg.time_span)

            supplied_range = support.Range(start_date_time, end_date_time, support.Range.RESOLUTION_DATETIME_MINUTE)
            supplied_resource = SuppliedUserInfo(supplied_range)

        return supplied_resource

    def __str__(self):
        return "Supplied User info " + SuppliedResource.__str__(self)


class SuppliedFlowData(SuppliedResource):
    def __init__(self, supplied_time_range):
        SuppliedResource.__init__(self, supplied_time_range)

    @staticmethod
    def from_bp_fetched_list_to_supplied_info(bp_fetched):
        times = map(lambda x: x.time, bp_fetched)
        min_time = min(*times)
        max_time = max(*times)

        return SuppliedFlowData(support.Range(min_time, max_time, 1))

    def __str__(self):
        return "Supplied Flow data " + SuppliedResource.__str__(self)


class SuppliedLinkCapacity(SuppliedResource):
    def __init__(self, supplied_link_id):
        SuppliedResource.__init__(self, supplied_link_id)

    @staticmethod
    def from_link_capacity_data_to_supplied_info(link_capacity_data):
        return SuppliedLinkCapacity(link_capacity_data.link_id)

    def __str__(self):
        return "Supplied Link capacity " + SuppliedResource.__str__(self)