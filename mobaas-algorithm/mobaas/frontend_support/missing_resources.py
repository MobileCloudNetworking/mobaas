from mobaas.frontend_support import supplied_resources as sr

'''
Each request received by the frontend may or may not
miss data in order to satisfy the request. As of such,
each piece of missing data is a missing resource which is
attached to the pending request.

Logic is also specified how to update the missing resource based
on its corresponding suppliedresource
'''

class MissingResource():
    supplied_resource = sr.SuppliedResource

    def __init__(self, missing):
        self.missing = missing

    def update_missing_from_supplied_info(self, supplied_info):
        return None

    def is_not_missing_anything(self):
        return not self.missing

    def __str__(self):
        return str(self.missing)

    def __repr__(self):
        return str(self)

    @staticmethod
    def update_missing_from_supplied_info_for_ranges(missing_resource, supplied_resource):
        supplied_range = supplied_resource.supplied
        new_missing = []

        for missing_range in missing_resource.missing:
            if missing_range.has_overlap(supplied_range):
                new_missing_range = missing_range - supplied_range
                new_missing.extend(new_missing_range)
            else:
                new_missing.append(missing_range)

        missing_resource.missing = new_missing


class MissingUserInfo(MissingResource):
    supplied_resource = sr.SuppliedUserInfo

    def __init__(self, missing_date_time_ranges):
        MissingResource.__init__(self, missing_date_time_ranges)

    def update_missing_from_supplied_info(self, supplied_user_info):
        MissingResource.update_missing_from_supplied_info_for_ranges(self, supplied_user_info)

    def __str__(self):
        return "Missing User info " + MissingResource.__str__(self)


class MissingFlowData(MissingResource):
    supplied_resource = sr.SuppliedFlowData

    def __init__(self, missing_time_ranges):
        MissingResource.__init__(self, missing_time_ranges)

    def update_missing_from_supplied_info(self, supplied_flow_data):
        MissingResource.update_missing_from_supplied_info_for_ranges(self, supplied_flow_data)

    def __str__(self):
        return "Missing Flow data " + MissingResource.__str__(self)


class MissingLinkCapacity(MissingResource):
    supplied_resource = sr.SuppliedLinkCapacity

    def __init__(self, missing_link_id):
        MissingResource.__init__(self, missing_link_id)

    def update_missing_from_supplied_info(self, supplied_link_capacity):
        if supplied_link_capacity.supplied == self.missing:
            self.missing = None

    def __str__(self):
        return "Missing Link capacity " + MissingResource.__str__(self)