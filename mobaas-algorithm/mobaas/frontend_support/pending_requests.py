from mobaas.common import error_logging as err

'''
A request may not have all data available it needs.
A request is then transformed into a pending request
and the missing data is added as a missing resource
to that pending request.

When a piece of information is received by MOBaaS from
the supplier, it is transformed into a supplied resource
and that range of data needs to be processed by each corresponding
pending request. So the function process_supplied_resource specifies
how to handle such a supplied resource and how to update its missing
resource with its new missing data range if any.
'''
class PendingRequest:
    def __init__(self, connection, request_message, missing_resources):
        self.connection = connection
        self.request_message = request_message
        self.missing_resources = {} #Keys are the corresponding supplied resources

        for missing_resource in missing_resources:
            self.add_missing_resource(missing_resource)

    def add_missing_resource(self, missing_resource):
        supplied_resource_key = missing_resource.supplied_resource

        if supplied_resource_key in self.missing_resources:
            self.missing_resources[supplied_resource_key].append(missing_resource)
        else:
            self.missing_resources[supplied_resource_key] = [missing_resource]

    def process_supplied_resource(self, supplied_resource):
        supplied_resource_key = supplied_resource.__class__

        if supplied_resource_key in self.missing_resources:
            missing_resources = self.missing_resources[supplied_resource_key]

            left_over_missing_resource = []

            for missing_resource in missing_resources:
                missing_resource.update_missing_from_supplied_info(supplied_resource)

                if not missing_resource.is_not_missing_anything():
                    left_over_missing_resource.append(missing_resource)

            if len(left_over_missing_resource) > 0:
                self.missing_resources[supplied_resource_key] = left_over_missing_resource
            else:
                del self.missing_resources[supplied_resource_key]

        else:
            err.log_error(err.ERROR, "Tried to process supplied_resource " + str(supplied_resource) + " but wasn't missing in " + str(self))

    def ready_to_be_handled(self):
        return len(self.missing_resources.items()) == 0

    def __str__(self):
        return "|PendingRequest {Request: " + str(self.request_message) + ", missing: " + str(self.missing_resources) + "}|"

    def __repr__(self):
        return str(self)


'''
Each pending request is put into the pending request queue.
It is a centralized object to process a supplied resource through
all pending requests and to get all requests that are ready to be handled.
'''
class PendingRequestQueue:
    def __init__(self):
        self.pending_requests = []

    def add_pending_request(self, connection, request_message, missing_resources):
        pending_request = PendingRequest(connection, request_message, missing_resources)

        self.pending_requests.append(pending_request)

    def process_supplied_resource(self, supplied_resource):
        for pending_request in self.pending_requests:
            pending_request.process_supplied_resource(supplied_resource)

    def get_ready_to_be_handled_requests(self):
        ready_to_be_handled = []
        not_ready_to_be_handled = []

        for pending_request in self.pending_requests:
            if pending_request.ready_to_be_handled():
                ready_to_be_handled.append(pending_request)
            else:
                not_ready_to_be_handled.append(pending_request)

        self.pending_requests = not_ready_to_be_handled

        return ready_to_be_handled

