#   Copyright 2014-2015 Zuercher Hochschule fuer Angewandte Wissenschaften
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import json
import logging
import os
from Queue import Queue
import requests
import time
import threading
import uuid

from occi.core_model import Link, Resource
from sdk import services
from sdk.mcn import util


BUNDLE_DIR = os.environ.get('OPENSHIFT_REPO_DIR', '.')
STG_FILE = 'service_manifest.json'
ITG_FILE = 'itg.yaml'


def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()


class Execution(object):
    """
    Interface to the CC methods. No decision is taken here on the service
    """

    def __init__(self, token, tenant):
        self.token = token
        self.tenant = tenant
        self.resolver = Resolver(token, tenant)

    def design(self):
        raise NotImplementedError()

    def deploy(self):
        raise NotImplementedError()

    def provision(self):
        raise NotImplementedError()

    def update(self, old, new, extras):
        raise NotImplementedError()

    def dispose(self):
        raise NotImplementedError()

    def state(self):
        raise NotImplementedError()

    def notify(self, entity, attributes, extras):
        pass


class Decision(object):

    def __init__(self, so_e, tenant, token):
        self.so_e = so_e
        self.tenant = tenant
        self.token = token

    def run(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()


#TODO add some sanity checks in the case no service manifest is present
class Resolver():

    def __init__(self, token, tenant):
        self.token = token
        self.tenant = tenant
        self.region = 'RegionOne'
        self.stg = None
        self.itg = None
        self.stack_id = None
        self.results_q = Queue()
        self.jobs = []
        self.service_inst_endpoints = [] # contains endpoint, type, attribs of instance

    def design(self):
        """
        Do initial design steps here.
        """
        with open(os.path.join(BUNDLE_DIR, 'data', STG_FILE)) as stg_content:
            self.stg = json.load(stg_content)
            stg_content.close()

        # TODO require better validation of the STG
        # e.g. current placing multiple services of the same type in the file will not work
        self.stg['depends_on'] = self.__sm_stg_ops(self.stg['depends_on'])

    def __get_endpoint(self, svc_type):
        # XXX note that currently all services in the service manifest must be in the same region!!!
        ep = services.get_service_endpoint(
            svc_type,
            self.token,
            tenant_name=self.tenant,
            region=self.region)
        return ep

    def __sm_stg_ops(self, svc_list):
        # purpose: take the stg and insert valid SM endpoints, maintain the input params of service
        svc_type_endpoint = []

        for svc_type in svc_list:
            if isinstance(svc_type, dict): # or isinstance(svc_type, unicode):
                # XXX if there are more than two keys this will be a prob
                ep = self.__get_endpoint(svc_type.keys()[0])
                if ep is None:
                    raise RuntimeError(svc_type.keys()[0] + ' endpoint could not be found - is the service registered?')
                LOG.info('* Service type: ' + svc_type.keys()[0].__repr__() + ' is instantiated at: ' + ep)

                # maintain inputs dict
                inputs = svc_type[svc_type.keys()[0]]['inputs']
                type_ep = {
                    svc_type.keys()[0]: {
                        'inputs': inputs,
                        'endpoint': ep
                    }
                }
                svc_type_endpoint.append(type_ep)
            else:
                LOG.info('stop feeding me crap!')
                raise RuntimeError('stop feeding me crap!')

        return svc_type_endpoint

    # deploy: only send instantiation requests
    # wait until all are complete
    # when all complete, store attributes against service type
    # then return control back to provision
    def deploy(self):
        """
        deploy service graph and infrastructure graph
        """

        LOG.info('============ DEPLOY ============')
        # create dependent services
        if len(self.stg['depends_on']) > 0:
            LOG.info('Deploying service dependencies...')
            self.__deploy_services(self.stg['depends_on'], self.jobs)

        # XXX this is a blocking operation and blocks the deploy call for the requester
        while len(self.jobs) != len(self.service_inst_endpoints):
            res = self.results_q.get()
            self.service_inst_endpoints.append(res)

        LOG.info('---> Creation of service dependencies is complete. Endpoints: ' + self.service_inst_endpoints.__repr__())
        LOG.info('---> All services are now deployed.')
        LOG.info('============ DEPLOY ============')

    def __deploy_services(self, services, jobs, svc_params={}):
        LOG.info('Deploying required services for ' + self.stg['service_type'])

        for dependent in services:
            if isinstance(dependent, dict):
                LOG.info('\t* ' + dependent.keys()[0] + ' -> ' + dependent[dependent.keys()[0]]['endpoint'])
                jobs.append(DeployTask(dependent, self.results_q, self.tenant, self.token, svc_params))
            else:  # TODO: re-enable serial deployments
                LOG.error('Something other than a dict was supplied. Support for serial deployments removed.')

        LOG.info('dependant services deployment requests ready!')

        # assumes that all creation requests mode (parallel|serial) are managed by DeployTask
        # XXX some throttling may be needed here - allow only 5 and then wait X secs to allow the next batch
        for job in jobs:
            job.start()

        LOG.info('Dependant services deployment requests sent!')

    def __get_services_rep(self, live):
        # This will be an update to all services with the necessary parameters
        heads = {'X-Auth-Token': self.token, 'X-Tenant-Name': self.tenant, 'Accept': 'application/occi+json'}
        if live:
            svc_reps = {}
            for svc_inst in self.service_inst_endpoints:
                for svc_url in svc_inst:
                    LOG.debug('Getting attributes for service instance: ' + svc_url['location'])
                    try:
                        r = requests.get(svc_url['location'], headers=heads)
                        r.raise_for_status()
                    except requests.HTTPError as err:
                        LOG.error('HTTP Error: should do something more here!' + err.message)
                        raise err
                    loc = svc_url['location']
                    attrs = json.loads(r.content)
                    occi_attrs = attrs['attributes']
                    srv_type = attrs['kind']['scheme'] + attrs['kind']['term']

                    # TODO multiple service instances per service provider
                    svc_reps[srv_type] = {'location': loc, 'attributes': occi_attrs}
        else:
            svc_reps = {u'http://schemas.mobile-cloud-networking.eu/occi/sm#test-dns': {'attributes': {u'mcn.service.state': u'provision', u'mcn.endpoint.dnsaas': u'10.0.0.1', u'mcn.endpoint.dns': u'10.0.0.1', u'occi.mcn.stack.state': u'CREATE_COMPLETE', u'activate.string': u'immutable_init_value', u'activate.float': u'0.11', u'occi.mcn.stack.id': u'9da3cb93-8e2b-4a78-ac47-b866954044b0', u'occi.core.id': u'54cd4aacac3c302522000287', u'activate.integer': u'1'}, 'location': 'http://160.85.4.53:8888/test-dns/54cd4aacac3c302522000287'}, u'http://schemas.mobile-cloud-networking.eu/occi/sm#test-maas': {'attributes': {u'mcn.service.state': u'provision', u'occi.mcn.stack.state': u'CREATE_COMPLETE', u'activate.string': u'immutable_init_value', u'activate.float': u'0.11', u'occi.mcn.stack.id': u'a36da3d3-9150-4ff5-91da-f3a702d5dddd', u'mcn.endpoint.maas': u'66.66.66.66', u'occi.core.id': u'54cd4abdac3c30252200029b', u'activate.integer': u'1'}, 'location': 'http://160.85.4.63:8888/test-maas/54cd4abdac3c30252200029b'}, u'http://schemas.mobile-cloud-networking.eu/occi/sm#test-epc': {'attributes': {u'mcn.endpoint.pdn-gw': u'10.0.0.1', u'mcn.service.state': u'provision', u'mcn.endpoint.srv-gw': u'10.0.0.1', u'occi.mcn.stack.state': u'CREATE_COMPLETE', u'mcn.endpoint.mme': u'10.0.0.1', u'activate.string': u'immutable_init_value', u'activate.float': u'0.11', u'occi.mcn.stack.id': u'e3e6f997-503b-40c6-9192-44d52ed45c04', u'activate.integer': u'1', u'mcn.endpoint.enodeb': u'10.0.0.1', u'occi.core.id': u'54cd4aceac3c3025220002af', u'mcn.endpoint.hss': u'10.0.0.1'}, 'location': 'http://160.85.4.60:8888/test-epc/54cd4aceac3c3025220002af'}}

        return svc_reps

    def provision(self, live=True):
        # XXX implementation should look for mutable parameters in receiving service
        # XXX and match with what's in existing service attrs

        LOG.info('============ PROVISION ============')

        # dirty hack - provision the DNS service in advance - will need monitoring ep
        # t_mon_ep = ''
        # for svc_iep in self.service_inst_endpoints:
        #     if svc_iep[0]['type'] == 'http://schemas.mobile-cloud-networking.eu/occi/sm#maas':
        #         t_mon_ep = svc_iep[0]['location']
        #         break
        # for svc_iep in self.service_inst_endpoints:
        #     if svc_iep[0]['type'] == 'http://schemas.mobile-cloud-networking.eu/occi/sm#dnsaas':
        #         heads = {'Content-type': 'text/occi',
        #                  'Accept': 'application/occi+json',
        #                  'X-Auth-Token': self.token,
        #                  'X-Tenant-Name': self.tenant}
        #         r = requests.get(t_mon_ep, headers=heads)
        #         r = json.loads(r.content)
        #         mon_ep = r['attributes']['mcn.endpoint.maas']
        #         heads['X-OCCI-Attribute'] = 'mcn.endpoint.maas="' + mon_ep + '"'
        #         r = requests.post(svc_iep[0]['location'], headers=heads)
        #         r.raise_for_status()
        #         break

        update_jobs = []
        svc_reps = self.__get_services_rep(live)

        # argh!!!! more dirty hacks!!!
        # this is to be removed, but
        # TODO pre and post operations should be supported for lifecycle
        # self.post_provision(svc_reps)

        # get params for each service
        for svc_type, svc_rep in svc_reps.iteritems():
            LOG.info('Getting parameters for: ' + svc_type)

            # get required param names from required services types
            params = self.__get_param_svc_type(svc_type)

            if len(params) <= 0 or svc_type == 'http://schemas.mobile-cloud-networking.eu/occi/sm#dnsaas':
                LOG.info(svc_type + ' does not need input parameters. No update needed.')
            else:
                LOG.info(svc_type + ' needs the following provisioning input parameters: ' + params.__repr__())
                occi_params = {}
                for param in params:
                    try:
                        # get the parameter value of the specified service type and parameter name
                        attr = svc_reps[param.keys()[0]]['attributes'][param[param.keys()[0]]]
                    except KeyError as ke:
                        LOG.error(param[param.keys()[0]] + ' of ' + param.keys()[0] +
                                  ' could not be found in the set of service parameters')
                        raise ke
                    LOG.info(svc_type + ' will be updated with: ' + param[param.keys()[0]] + ' = ' + attr)
                    occi_params[param[param.keys()[0]]] = attr

                LOG.debug('Parameters ' + occi_params.__repr__() + ' for ' + svc_type + ' instance at: '
                          + svc_rep['location'])
                update_job = {'params': occi_params, 'inst_ep': svc_rep['location']}
                update_jobs.append(update_job)

        queue = Queue()
        for update_job in update_jobs:
            pt = ProvisionTask(self.tenant, self.token, update_job, queue)
            pt.start()

        prov_results = []
        while len(update_jobs) != len(prov_results):
            res = queue.get()
            prov_results.append(res)

        LOG.info('---> All services and resources are now provisioned.')

        # post-provision logic
        # self.post_provision(svc_reps)

        LOG.info('============ PROVISION ============')

    # def post_provision(self, svc_reps):
    #     if 'http://schemas.mobile-cloud-networking.eu/occi/sm#dnsaas' in svc_reps:
    #         # configure DNS
    #         svc_loc = svc_reps['http://schemas.mobile-cloud-networking.eu/occi/sm#dnsaas']['location']
    #         heads = {'Content-type': 'text/occi',
    #                  'Accept': 'application/occi+json',
    #                  'X-Auth-Token': self.token,
    #                  'X-Tenant-Name': self.tenant}
    #         r = requests.get(svc_loc, headers=heads)
    #         r = json.loads(r.content)
    #         api = r['attributes']['mcn.endpoint.api']
    #         fwdr = r['attributes']['mcn.endpoint.forwarder']
    #
    #         LOG.debug('DNS API: ' + api)
    #         LOG.debug('DNS Forwarder: ' + fwdr)
    #         # DNSaaSClient.DNSaaSClientCore.apiurlDNSaaS = 'http://' + api + ':8080'
    #
    #         domain = 'epc.mnc001.mcc001.3gppnetwork.org'
    #         LOG.info('Creating DNS Domain... ' + domain)
    #         is_ready = False
    #         while not is_ready:
    #             # result = DNSaaSClient.createDomain(domain,
    #             #                                    'admin@mcn.pt',
    #             #                                    tokenId=self.token)
    #             if result == "Server API not reachable":
    #                 LOG.warn('DNS Service not ready to provide service yet.')
    #                 time.sleep(13)  # wait for the API to become available
    #             else:
    #                 is_ready = True
    #                 # LOG.debug('Result of create domain: ' + result.__repr__())

    def __get_param_svc_type(self, svc_type):
        svc_params = []
        for req in self.stg['depends_on']:
            if req.keys()[0] == svc_type:
                for y in req[req.keys()[0]]['inputs']:
                    supply_service = y.split('#')
                    svc_params.append({supply_service[0] + '#' + supply_service[1]: supply_service[2]})
        # remove duplicate dicts from the list
        result = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in svc_params)]
        # results contain the service type from where the attribute value can be found
        return result

    def update(self):
            pass

    def dispose(self):
        """
        Dispose SICs.
        """
        LOG.info('============ DISPOSE ============')
        # destroy the services
        for job in self.jobs:
            job.destroy()

        LOG.info('============ DISPOSE ============')

    def __get_service_dependencies(self):

        # service_inst_endpoints = [[{'attributes': {'mcn.service.state': 'provision', 'mcn.endpoint.dnsaas': '10.0.0.1', 'mcn.endpoint.dns': '10.0.0.1', 'occi.mcn.stack.state': 'CREATE_COMPLETE', 'activate.string': 'immutable_init_value', 'activate.float': '0.11', 'occi.mcn.stack.id': '045be956-59d6-4c55-96f4-9be7708ead5e', 'occi.core.id': '54ce1261ac3c30252200037a', 'activate.integer': '1'}, 'type': u'http://schemas.mobile-cloud-networking.eu/occi/sm#test-dns', 'location': 'http://160.85.4.53:8888/test-dns/54ce1261ac3c30252200037a'}], [{'attributes': {'mcn.service.state': 'provision', 'mcn.endpoint.enodeb': '10.0.0.1', 'mcn.endpoint.pdn-gw': '10.0.0.1', 'occi.mcn.stack.state': 'CREATE_COMPLETE', 'mcn.endpoint.mme': '10.0.0.1', 'activate.string': 'immutable_init_value', 'activate.float': '0.11', 'occi.mcn.stack.id': '0ae232ad-b387-463d-9597-590d6ef61f56', 'mcn.endpoint.hss': '10.0.0.1', 'mcn.endpoint.srv-gw': '10.0.0.1', 'occi.core.id': '54ce1273ac3c30252200038e', 'activate.integer': '1'}, 'type': u'http://schemas.mobile-cloud-networking.eu/occi/sm#test-epc', 'location': 'http://160.85.4.60:8888/test-epc/54ce1273ac3c30252200038e'}], [{'attributes': {'mcn.service.state': 'provision', 'occi.mcn.stack.state': 'CREATE_COMPLETE', 'activate.string': 'immutable_init_value', 'activate.float': '0.11', 'occi.mcn.stack.id': '3e67b283-971b-461b-8b96-3994954200ce', 'mcn.endpoint.maas': '66.66.66.66', 'occi.core.id': '54ce1285ac3c3025220003a2', 'activate.integer': '1'}, 'type': u'http://schemas.mobile-cloud-networking.eu/occi/sm#test-maas', 'location': 'http://160.85.4.63:8888/test-maas/54ce1285ac3c3025220003a2'}]]
        links = []

        for svcs in self.service_inst_endpoints:
            for svc in svcs:
                deps = self.__get_dependent_service(svc['type'], self.stg['depends_on'])

                links.append({'location': svc['location'], 'type': svc['type'], 'deps': deps})

        # find dependent service instance endpoint
        for link in links:
            deps_locs = {}
            for dep in link['deps']:
                for svcs in self.service_inst_endpoints:
                    for svc in svcs:
                        if svc['type'] == dep:
                            deps_locs[dep] = svc['location'],
            link['deps'] = deps_locs

        return links

    def __get_dependent_service(self, svc, stg_deps):

        dep_svcs = set()

        for deps in stg_deps:
            for k, v in deps.iteritems():
                if k == svc:
                    for dep in v['inputs']:
                        dep = dep.split('#')[0] + '#' + dep.split('#')[1]
                        dep_svcs.add(dep)
        return dep_svcs

    def __get_occi_links(self, svcs_deps):
        links = []
        for svcs_dep in svcs_deps:
            source = Resource(svcs_dep['location'], Resource.kind, [])
            for _, v in svcs_dep['deps'].iteritems():
                target = Resource(v[0], Resource.kind, [])
                links.append(Link(str(uuid.uuid4()), Link.kind, [], source, target))
        return links

    # state of composition
    def state(self):
        """
        Report on state.
        """

        # TODO as the resolver creates one or more instances, it would make sense to
        # TODO group parameters by service type and include the service endpoint

        LOG.info('============ STATE ============')
        # for each service endpoint get their details and merge into one big dict
        # get the state of the heat template that may be part of this service
        attrs_list = []
        heads = {'Content-type': 'text/occi',
                 'Accept': 'application/occi+json',
                 'X-Auth-Token': self.token,
                 'X-Tenant-Name': self.tenant}

        for svc_inst in self.service_inst_endpoints:
            for svc_url in svc_inst:
                try:
                    r = requests.get(svc_url['location'], headers=heads)
                except requests.HTTPError as err:
                    LOG.info('HTTP Error: should do something more here!' + err.message)
                    raise err
                content = json.loads(r.content)
                attrs_list.append(content['attributes'])

        a_out = {}
        for attr in attrs_list:
            for k, v in attr.items():
                a_out[k] = v

        insts = ''
        for svcs in self.service_inst_endpoints:
            for svc in svcs:
                # deps = self.__get_dependent_service(svc['type'], self.stg['depends_on'])
                insts = insts + svc['location'] + ' '
        insts = insts[0:-1]
        a_out['mcn.so.svcinsts'] = insts

        LOG.info('Attributes of E2E service: ' + a_out.__repr__())

        LOG.info('============ STATE ============')
        return a_out


class ProvisionTask(threading.Thread):

    def __init__(self, tenant, token, update_job, results_q):
        super(ProvisionTask, self).__init__()
        self.tenant = tenant
        self.token = token
        self.update_job = update_job
        self.q = results_q

    def run(self):
        super(ProvisionTask, self).run()

        heads = {'X-Auth-Token': self.token, 'X-Tenant-Name': self.tenant, 'Content-type': 'text/occi'}
        iep = self.update_job['inst_ep']
        attrs = ''
        for k, v in self.update_job['params'].iteritems():
            attrs = attrs + k + '="' + v + '", '
        heads['X-OCCI-Attribute'] = attrs[0:-2]

        LOG.info('Provisioning service instance: ' + iep)
        LOG.info('Sending headers: ' + heads.__repr__())

        try:
            r = requests.post(iep, headers=heads)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err

        ready = False
        while not ready:
            ready, r = self.is_ready(iep)
            time.sleep(13)  # TODO how best to set this timeout? configfile for now?

        self.q.put(r)

    def is_ready(self, loc):
        heads = {
            'Content-type': 'text/occi',
            'Accept': 'text/occi',
            'X-Auth-Token': self.token,
            'X-Tenant-Name': self.tenant,
        }

        LOG.info('checking service state at: ' + loc)
        LOG.info('sending headers: ' + heads.__repr__())
        try:
            r = requests.get(loc, headers=heads)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.info('HTTP Error: should do something more here!' + err.message)
            raise err

        attrs = r.headers.get('x-occi-attribute', '')

        if len(attrs) > 0:
            attr_hash = self.attr_string_to_dict(attrs)
            stack_state = ''
            try:
                stack_state = attr_hash['occi.mcn.stack.state']
            except KeyError:
                pass

            LOG.info('Current service state: ' + attr_hash['mcn.service.state'])
            if attr_hash['mcn.service.state'] == 'update' and stack_state == 'CREATE_COMPLETE':
                LOG.info('Service is ready')
                return True, r
            else:
                LOG.info('Service is not ready')
                return False, r

    def attr_string_to_dict(self, attrs_string):
        attr_hash = {}
        if len(attrs_string) <= 0:
            LOG.warn('Attributes string is empty.')
        else:
            for kv in attrs_string.split(','):
                key = kv.strip().split('=')[0]
                val = kv.strip().split('=')[1]
                if val.endswith('\'') or val.endswith('"'):
                    val = val[1:-1]
                attr_hash[key] = val

        LOG.info('attributes extracted: ' + attr_hash.__repr__())
        return attr_hash


class DeployTask(threading.Thread):
    # will provision one service or an array of services.
    # if an array is presented, then these services are to be processed in series
    # This task will only report completion (through a queue) when the service instance enters
    # into the 'active' state.
    # The same logic applies should an ordered list of services be supplied but in this case
    # the result is reported when all services in the array enter into the 'active' state
    # XXX This can be a long running task - needs audit log
    def __init__(self, service_spec, results_q, tenant, token, svc_params):
        super(DeployTask, self).__init__()
        self.service_spec = service_spec
        self.q = results_q
        self.tenant = tenant
        self.token = token
        self.endpoints = []
        self.svc_params = svc_params

    def run(self):
        super(DeployTask, self).run()

        LOG.info('provisioning: ' + self.service_spec.__repr__())

        # all block until the service has entered it's 'active' phase
        # the service spec is a list of hashes, therefore is a set of services to be executed sequentially
        # if isinstance(self.service_spec, list):
        #     LOG.info('provisioning services in series')
        #     for srv in self.service_spec:
        #         srv_inst = self.create_service(srv)
        #         LOG.info('created the service: ' + srv_inst.__repr__())
        #         self.endpoints.append(srv_inst)
        if isinstance(self.service_spec, dict):  # just a singular service TODO re-enable serial reqs?
            srv_inst = self.create_service(self.service_spec)
            LOG.info('created the service: ' + srv_inst.__repr__())
            self.endpoints.append(srv_inst)
        else:
            LOG.info('Stop feeding me crap!')
            raise RuntimeError('stop feeding me crap!')

        # signal that this thread is complete. len(result) should be >= 1
        self.q.put(self.endpoints)

    def create_service(self, service_spec):
        srv_type = service_spec.keys()[0]
        heads = {
            'Category': srv_type.split('#')[1] + '; ' + 'scheme="' + srv_type.split('#')[0] + '#"; class="kind"',
            'Content-type': 'text/occi',
            'Accept': 'text/occi',
            'X-Auth-Token': self.token,
            'X-Tenant-Name': self.tenant,
        }

        if len(self.svc_params) > 0:
            LOG.info('Sending additional parameters to service: ' + self.svc_params.__repr__())

            occi_attr = ''
            for para_k, para_v in self.svc_params.items():
                occi_attr = para_k + '="' + para_v + '", '

            heads['X-OCCI-Attribute'] = occi_attr[0:-2]

        try:
            LOG.info('issuing service instantiation to: ' + service_spec[srv_type]['endpoint'])
            LOG.info('issuing service instantiation with headers: ' + heads.__repr__())
            r = requests.post(service_spec[srv_type]['endpoint'], headers=heads)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.info('HTTP Error: should do something more here!' + err.message)
            raise err

        # at this point, the request will return back an X-OCCI-Location, the service has not completed it's process
        loc = r.headers.get('Location', '')
        if loc == '':
            LOG.error('No OCCI location for the service instance found.')
            raise RuntimeError('No OCCI location for the service instance found.')

        # wait for the service to enter into the active
        ready = False
        while not ready:
            ready, r = self.is_ready(loc)
            time.sleep(13)  # TODO how best to set this timeout? configfile for now?

        # TODO here is where we place attributes against the location to the service
        attrs_string = r.headers.get('x-occi-attribute', '')
        attrs = self.attr_string_to_dict(attrs_string)

        LOG.info('Service instantiated: ' + loc)
        LOG.info('Service attributes are: ' + attrs.__repr__())

        return {'type': srv_type, 'location': loc, 'attributes': attrs}

    def is_ready(self, loc):
        heads = {
            'Content-type': 'text/occi',
            'Accept': 'text/occi',
            'X-Auth-Token': self.token,
            'X-Tenant-Name': self.tenant,
        }

        LOG.info('checking service state at: ' + loc)
        LOG.info('sending headers: ' + heads.__repr__())
        try:
            r = requests.get(loc, headers=heads)
            r.raise_for_status()
        except requests.HTTPError as err:
            LOG.info('HTTP Error: should do something more here!' + err.message)
            raise err

        attrs = r.headers.get('x-occi-attribute', '')

        if len(attrs) > 0:
            attr_hash = self.attr_string_to_dict(attrs)
            stack_state = ''
            try:
                stack_state = attr_hash['occi.mcn.stack.state']
            except KeyError:
                pass

            # XXX This is where things must work!
            LOG.info('Current service state: ' + attr_hash['mcn.service.state'])
            if attr_hash['mcn.service.state'] == 'provision' and stack_state == 'CREATE_COMPLETE':
                LOG.info('Service is ready')
                return True, r
            else:
                LOG.info('Service is not ready')
                return False, r

    def attr_string_to_dict(self, attrs_string):
        attr_hash = {}
        if len(attrs_string) <= 0:
            LOG.warn('Attributes string is empty.')
        else:
            for kv in attrs_string.split(','):
                key = kv.strip().split('=')[0]
                val = kv.strip().split('=')[1]
                if val.endswith('\'') or val.endswith('"'):
                    val = val[1:-1]
                attr_hash[key] = val

        LOG.info('attributes extracted: ' + attr_hash.__repr__())
        return attr_hash

    def destroy(self):
        heads = {'Content-Type': 'text/occi',
                 'X-Auth-Token': self.token,
                 'X-Tenant-Name': self.tenant
        }
        for ep in self.endpoints:
            LOG.info('Destroying service: ' + ep['location'])
            LOG.info('Sending headers: ' + heads.__repr__())
            try:
                r = requests.delete(ep['location'], headers=heads)
                r.raise_for_status()
            except requests.HTTPError as err:
                LOG.info('HTTP Error: should do something more here!' + err.message)
                raise err

# basic test
if __name__ == '__main__':

    token = 'e383301a2ae5492ba168a9e50968eecd'
    tenant = 'edmo'

    res = Resolver(token, tenant)
    res.design()
    res.deploy()
    res.provision(live=True)

    # LOG.info('instantiated service dependencies: ' + res.service_inst_endpoints.__repr__())
    # # LOG.info('instantiated resource dependencies (heat stack id): ' + res.stack_id)
    stack_output = res.state()
    LOG.info('stack output: ' + stack_output.__repr__())

    res.dispose()
