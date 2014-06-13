# MCN Service Manger

This is the MCN Service Manager

An example and naive example of an EPC Service Manager can be found in ./example
For service manager implementers they simply need to follow this example for their own service.

You can run this example by `python ./example/demo_service_manager.py`

The SM library is under mcn/sm

The example service manager (`example/demo_service_manager.py`) uses and extends this library.

## Authentication
Authentication and access to the SM is mediated by OpenStack keystone. In order to make a service instantiation request
against a SM the end user needs to supply:

 * tenant name: this should be provided through the `X-Auth-Token` HTTP header
 * token: this should be provided through the `X-Tenant-Name` HTTP header. If no `X-Tenant-Name` is supplied the default of `admin` will be used (See [here](https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_cc_sdk/blob/master/sdk/services.py#L86) for why).

### Generating a Keystone Token
**IMPORTANT:** you're user must be assigned `admin` permissions for the project they're part of.

For this to work you will need the keystone command line tools installed (`pip install python-keystoneclient`) and also your OpenStack credentials.

To create a keystone token issue the following commands:

    $ keystone token-get

## Configuration

All configuration of the service manager is carried out through `etc/sm.cfg`. There are three sections to this
configuration file.

 * `general` - this configuration is used by the code under the namespace of mcn.sm.
 * `service_manager` - this is configuration related to the service manager that you implement
 * `service_manager_admin` - this section is related to the registration of the service with keystone
 * `cloud_controller` - configuration related to the cloudcontroller

Please see the configuration file `etc/sm.cfg` for further parameter descriptions.
This service manager framework assumes that the bundle supplied will be deployed using git.

### Configuration of demo SO bundle

There are some support files that the SM and the CC rely upon. These support files must be stored under the root of
your SO bundle in a folder named `support`.

If you wish to run the example you will possibly have to update one of them.

The `support/pre_start_python` file contains a variable that points to the AAA service. For this demo, the URI value of
`DESIGN_URI` should be set to your OpenStack keystone API e.g. `http://$KEYSTONE_HOST:5000/v2.0`.

There is no further configuration needed for the bundle.

### Cavaets

 * Make sure that for the user running the SM process that the following line appears in `~/.ssh/config`

        StrictHostKeyChecking no

## Usage

To see what services are available by the service provider you need to query the service registry.

    $ curl -v -X GET http://localhost:8888/-/

To create an instance of a service offered by the service provider (e.g. using the EPC demo service manager).

    $ curl -v -X POST http://localhost:8888/epc/ -H 'Category: epc; scheme="http://schemas.mobile-cloud-networking.eu/occi/sm#"; class="kind";' -H 'content-type: text/occi' -H 'x-tenant-name: YOUR_TENANT_NAME' -H 'x-auth-token: YOUR_KEYSTONE_TOKEN'

This request, if successful, will return a service instance ID that can be used to request further details about the
service instance.

    $ curl -v -X GET http://localhost:8888/epc/59eb41f9-8cbc-4bbd-bb16-4101703d0e13 -H 'x-tenant-name: YOUR_TENANT_NAME' -H 'x-auth-token: YOUR_KEYSTONE_TOKEN'

To dispose of the instance you can issue the following request.

    $ curl -v -X DELETE http://localhost:8888/epc/59eb41f9-8cbc-4bbd-bb16-4101703d0e13 -H 'x-tenant-name: YOUR_TENANT_NAME' -H 'x-auth-token: YOUR_KEYSTONE_TOKEN'

### Authentication
To authentication you need to supply a tenant name and token. Do this by setting the following HTTP headers in your request

 * X-Tenant-Name
 * X-Auth-Token

## Quickly Getting Started

1. Clone [this project](https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_sm)

2. Install the service manager library:

        $ python ./setup.py install

3. Use the example service manager as your starting point (`example/demo_service_manager.py`). Add your service type definition. For example:

        my_svc_type = Type('http://schemas.mobile-cloud-networking.eu/occi/sm#',
        'mysvc',
        title='My service',
        attributes={
                   'mcn.my.admin_password': 'mutable',
                    },
        related=[Resource.kind],
        actions=[])

4. Take a copy of `etc/sm.cfg` and customise it according to your own service (e.g. setting the path to your SO bundle)

5. Edit the existing SO implementation and make it work for you.

5. Run your service manager. Example using the demo:

        $ python ./demo_service_manager.py -c ../etc/sm.cfg

## Dependency notes

You must have the latest version of pyssf installed. To ensure you have the latest (> 0.4.8) you can install it from source.

    $ git clone https://github.com/tmetsch/pyssf.git
    $ cd pyssf
    $ python ./setup.py install
