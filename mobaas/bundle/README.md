# Testing SO without deploying it using CC
#
Goto the directory of mcn_cc_sdk & setup virtenv (Note: could be done easier):

    $ virtualenv /tmp/mcn_test_virt
    $ source /tmp/mcn_test_virt/bin/activate

Install SDK and required packages:

    $ pip install pbr six iso8601 babel requests python-heatclient==0.2.9 python-keystoneclient
    $ python setup.py install  # in the mcn_cc_sdk directory.

Run SO:

    $ export OPENSHIFT_PYTHON_DIR=/tmp/mcn_test_virt
    $ export OPENSHIFT_REPO_DIR=<path to ICNaaS SO>
    $ python ./wsgi/application

Optionally you can also set the DESIGN_URI if your OpenStack install is not local.

In a new terminal do get a token from keystone (token must belong to a user which has the admin role for the tenant):

    $ keystone token-get
    $ export KID='...'
    $ export TENANT='...'

You can now visit the SO interface [here](http://localhost:8051/orchestrator/default).

## Sample requests

Initialize the SO:

    $ curl -v -X PUT http://localhost:8051/orchestrator/default \
          -H 'Content-Type: text/occi' \
          -H 'Category: orchestrator; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
          -H 'X-Auth-Token: '$KID \
          -H 'X-Tenant-Name: '$TENANT

Get state of the SO + service instance:

    $ curl -v -X GET http://localhost:8051/orchestrator/default \
          -H 'X-Auth-Token: '$KID \
          -H 'X-Tenant-Name: '$TENANT

Trigger deployment of the service instance:

    $ curl -v -X POST http://localhost:8051/orchestrator/default?action=deploy \
          -H 'Content-Type: text/occi' \
          -H 'Category: deploy; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
          -H 'X-Auth-Token: '$KID \
          -H 'X-Tenant-Name: '$TENANT

Trigger provisioning of the service instance:

    $ curl -v -X POST http://localhost:8051/orchestrator/default?action=provision \
          -H 'Content-Type: text/occi' \
          -H 'Category: provision; scheme="http://schemas.mobile-cloud-networking.eu/occi/service#"' \
          -H 'X-Auth-Token: '$KID \
          -H 'X-Tenant-Name: '$TENANT

Trigger update on SO + service instance:

    $ curl -v -X POST http://localhost:8051/orchestrator/default \
          -H 'Content-Type: text/occi' \
          -H 'X-Auth-Token: '$KID \
          -H 'X-Tenant-Name: '$TENANT \
          -H 'X-OCCI-Attribute: occi.epc.attr_1="foo"'

Trigger delete of SO + service instance:

    $ curl -v -X DELETE http://localhost:8051/orchestrator/default \
          -H 'X-Auth-Token: '$KID \
          -H 'X-Tenant-Name: '$TENANT
