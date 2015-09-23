# MCN Service Manger
#
**NOTE: THIS DOCUMENTATION REQUIRES UPDATES!!!**

## Quickly Getting Started

This is the MCN Service Manager.

To checkout the code and also setup the example SO, do the following:

    $ git clone git@git.mobile-cloud-networking.eu:cloudcontroller/mcn_sm.git
    $ cd mcn_sm
    $ git submodule init
    $ git submodule update
    
The latest version of the MCN Service Manager is a library which needs to be installed.

	$ python setup.py install

An example of a simple Service definition can be found in `./example`
For service manager implementers they simply need to follow this example for their own service.

You can run this example by `python bin/service_manager.py -c etc/sm.cfg`, after properly updating the config file under etc/sm.cfg. In particular replace absolute paths with your own values.

The SM library is under the `sm` directory.

The example service manager (`example/data/service_manifest.json`) uses and extends this library.

## Upfront Notice

This is important. The SM will **only** deploy the SO's code that is on its `master` branch.

## Further Documentation

1. Clone [this project](https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_sm)

2. Install the service manager library:

        $ python ./setup.py install

3. Use the example service manifest as your starting point (`example/data/service_manifest.json`). Edit your service type 
definition. For example:

        {
    	    "service_type": "http://schemas.mobile-cloud-networking.eu/occi/sm#test-compo",
    	    "service_description": "Test composed service",
    	    "service_attributes": {
    	        "mcn.endpoint.p3": "immutable",
    	        "mcn.endpoint.p4": "immutable"
    	    },
    	    "service_endpoint": "http://127.0.0.1:8888/test-compo/",
    	    "depends_on": [
              { "http://schemas.mobile-cloud-networking.eu/occi/sm#demo1": { "inputs": [] } },
              { "http://schemas.mobile-cloud-networking.eu/occi/sm#demo2": {
                  "inputs": [
                    "http://schemas.mobile-cloud-networking.eu/occi/sm#demo1#mcn.endpoint.p1"
                  ] }
              }
            ],
    	}
    	
    Compared to the previous version of the service manager, attributes which were in the typical `my_service_sm.py`, service type, description and attributes are all located in the service manifest json file, but are otherwise unchanged.
    
    The `service_endpoint` value will be the url of the new service as registered on Keystone for the corresponding service type. This is only used if the register_service parameter is set to True in the configuration file sm.cfg.
    
    The `depends_on` list specifies which services are necessary for the new service to be properly configured, but will not be exposed to external users. They are internal dependencies which can either require no input (atomic services), or require some input parameters from one of the other dependencies.
    
    In the example above,
        
        { "http://schemas.mobile-cloud-networking.eu/occi/sm#demo2": {
            "inputs": [
                "http://schemas.mobile-cloud-networking.eu/occi/sm#demo1#mcn.endpoint.p1"
            ] 
        }
    the `demo2` service requires a parameter named `mcn.endpoint.p1` from the `demo1` service. 
    
    Using depends on allows automatic deployment and provisioning of all service dependencies, so that it is not necessary to create them manually in a new SO. 
    
    On the other hand, to actually retrieve the endpoints and generally attributes of the service dependencies, you **must** use the Resolver class as defined in the service_orchestrator.py file. More details in the corresponding section.

4. Take a copy of `etc/sm.cfg` and customise it according to your own service (e.g. setting the path to your SO bundle as well as to the Service Manifest)

5. Edit the existing SO implementation and make it work for you.

5. Run your service manager. Example using the demo:

        $ python bin/service_manager.py -c etc/sm.cfg
        
### Resolver

The resolver's role is to manage the lifecycle of the service dependencies of a given service. To take advantage of this, a SO implementation execution **must** inherit from `service_orchestrator.Execution`. 

From a SO, it is easy to retrieve attributes from the created service dependencies by accessing the retriever's `service_inst_endpoints` class attribute as an array of service attributes. This is shown in the sample SO example.

    LOG.info(self.resolver.service_inst_endpoints)
    
The SO is then free to use these deployed services as required.

## Logging

The Service Manager now includes a way to also send logs to a Graylog2 server on top of the default file logging, for easier log search and visualisation. To use this functionality, edit the following configuration within the general section of sm.cfg:

    [general]
    # This is the path and file name of where the SM's log file is stored.
    # required; default: sm.log string
    log_file=sm.log
    # hostname of where the Graylog2 server is running at
    graylog_api=log.cloudcomplab.ch
    # UDP Port of the Graylog2 server (for UDP sources)
    graylog_port=12201
    
It is also possible to send logs from within a SO instance running on openshift. A simple implementation is as follows in the top section of a so implementation:

    from sm.so.service_orchestrator import LOG
    gray_handler = graypy.GELFHandler("log.cloudcomplab.ch",
                                      12201,
                                      localname=os.environ['OPENSHIFT_GEAR_DNS'])
    LOG.addHandler(gray_handler)

This example is illustrated in the mcn_sample_runtime_so example of service available in the mcn_sample_so repo. Do not omit the localname parameter as otherwise all openshift instances will appear with the hostname master.ops.cloudcomplab.ch on Graylog.

## Authentication
Authentication and access to the SM is mediated by OpenStack keystone. In order to make a service instantiation request
against a SM the end user needs to supply:

 * tenant name: this should be provided through the `X-Auth-Token` HTTP header
 * token: this should be provided through the `X-Tenant-Name` HTTP header. If no `X-Tenant-Name` is supplied the 
 default of `admin` will be used (See [here](https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_cc_sdk/blob/master/sdk/services.py#L86) for why).

### Generating a Keystone Token
**IMPORTANT:** your user must be assigned `admin` permissions for the project they're part of.

For this to work you will need the keystone command line tools installed (`pip install python-keystoneclient`) 
and also your OpenStack credentials.

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

### Service Provider Internal Parameters
If the service provider needs to pass parameters to various stages of the instantiation process, this can be done by
adding those parameters to a JSON file. There is an example of this in `etc/service_params.json`

### Configuration of demo SO bundle

The demo SO bundle comes from: https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_sample_so It is added as a 
submodule and can be retreived using the above instructions.

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
To authentication you need to supply a tenant name and token. Do this by setting the following HTTP headers in your 
request

 * X-Tenant-Name
 * X-Auth-Token

## Dependency notes

1. You must have the MCN SDK installed on the machine where you run your service manager. To do so:

        $ git clone git@git.mobile-cloud-networking.eu:cloudcontroller/mcn_cc_sdk.git
        $ cd mcn_cc_sdk
        $ python ./setup.py install

## Questions?

Give edmo@zhaw.ch a mail
