# Testing SO without deploying it using CC

Goto the directory of mcn_cc_sdk & setup virtenv (Note: could be done easier):

    $ virtualenv /tmp/mcn_test_virt
    $ source /tmp/mcn_test_virt/bin/activate

Install SDK and required packages:

    $ pip install pbr six iso8601 babel requests python-heatclient python-keystoneclient
    $ python setup.py install

Run SO:

    $ cd misc/sample_so
    $ export OPENSHIFT_PYTHON_DIR=/tmp/mcn_test_virt
    $ export OPENSHIFT_REPO_DIR=<path to sample so>
    $ python ./wsgi/application

In a new terminal do get a token from keystone:

    $ keystone token-get
    $ export KID='...'

You can now visit the SO interface at [here](localhost:8051):

    $ curl -X POST localhost:8051/action=init -H 'Auth-Token: '$KID
    $ curl -X GET localhost:8051/
    $ curl -X GET localhost:8051/state
    $ curl -X POST localhost:8051/action=deploy
    $ curl -X POST localhost:8051/action=dispose

# SM Notes

You must have a directory `support` with the contents that are present in this demonstrator