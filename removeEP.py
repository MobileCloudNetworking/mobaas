# A piece of code to get the list of registered services on keystone
# Execution example: python listEP.py <USERNAME> <PASSWORD> <TENANT_NAME> <AUTH_URL>

__author__ = 'Mohammad'

import sys
import getopt

from keystoneclient.v2_0 import client

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hs:u:p:t:a:",["service_id=","username=","password=","tenant_name=","auth_url="])
    except getopt.GetoptError:
        print 'Usage: python removeEP.py -s <SERVICE_ID> -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL]'
        exit(0)

    user_name = None
    passwd = None
    tenant_name = None
    auth_url = None
    s_id = None

    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: python removeEP.py -s <ENDPOINT_ID> -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL]'
            exit(0)
        elif opt in ("-u", "--username"):
            user_name = arg
        elif opt in ("-p", "--password"):
            passwd = arg
        elif opt in ("-t", "--tenant_name"):
            tenant_name = arg
        elif opt in ("-a", "--auth_url"):
            auth_url = arg
        elif opt in ("-s", "--service_id"):
            s_id = arg

    if user_name is None:
        user_name = 'zhao'

    if passwd is None:
        passwd = '19831030forever!'

    if tenant_name is None:
        tenant_name = 'uni-bern'

    if auth_url is None:
        auth_url = 'http://bart.cloudcomplab.ch:35357/v2.0'

    if s_id is None:
        print 'Service ID is mandatory!'
        exit(0)

    keystone = client.Client(username=user_name, password=passwd, tenant_name=tenant_name, auth_url=auth_url)

    service_list = keystone.services.list()

    for item in service_list:
        if item._info['id'] == s_id:
            res = keystone.services.delete(s_id)
            print res.__repr__()
            return 1

    print "Service not found."

if __name__ == "__main__":
    main(sys.argv[1:])
