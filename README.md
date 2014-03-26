# MCN Service Manger

This is the MCN Service Manager

An example and naive example of an EPC Service Manager can be found in ./example
For service manager implementers they simply need to follow this example for their own service.

You can run this example by `python ./example/demo_service_manager.py`

The SM library is under mcn/sm

The example uses and extends this library

## Configuration

All configuration of the service manager is carried out through `etc/sm.cfg`. There are three sections to this
configuration file.

 * `general` - this configuration is used by the code under the namespace of mcn.sm.
   * `port`: the port number on which the service manager listens
 * `service_manager` - this is configuration related to the service manager that you implement
   * `bundle_location`: this is where your service orchestrator bundle is located. Currently **only** file path locations are supported
 * `cloud_controller`
   * `nb_api`: The URL to the North-bound API of the [CloudController](https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_cc_api)

This service manager framework assumes that the bundle supplied will be deployed using git.

### Cavaets

 * Make sure that for the user running the SM process that the following line appears in `~/.ssh/config`

        StrictHostKeyChecking no


## Usage

To see what services are available by the service provider you need to query the service registry.

    $ curl -v -X GET http://localhost:8888/-/

To create an instance of a service offered by the service provider (e.g. using the EPC demo service manager).

    $ curl -v -X POST http://localhost:8888/epc/ -H 'Category: epc; scheme="http://schemas.mobile-cloud-networking.eu/occi/sm#"; class="kind";' -H 'content-type: text/occi'

This request, if successful, will return a service instance ID that can be used to request further details about the
service instance.

    $ curl -v -X GET http://localhost:8888/epc/59eb41f9-8cbc-4bbd-bb16-4101703d0e13

To dispose of the instance you can issue the following request.

    $ curl -v -X DELETE http://localhost:8888/epc/59eb41f9-8cbc-4bbd-bb16-4101703d0e13

