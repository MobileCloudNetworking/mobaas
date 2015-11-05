.PHONY: default install_flows_ts_module

default: install_flows_ts_module

install_flows_ts_module:
	@ python setup.py build
	@ sudo python setup.py install --record installed_files.txt

remove:
	@ sudo cat installed_files.txt | xargs rm -rf
	@ rm -rf installed_files.txt
