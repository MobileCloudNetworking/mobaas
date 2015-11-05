.PHONY: default pip python-enum sql_server sql_python_driver create_mcn_user create_databases remove_databases remove_user remove_sql_server remove_sql_python_driver remove self_test self_test_setup self_text_exec self_test_cleanup

#SQL Related
root_password = mcn_MOBaaS
mcn_user_name = mcn_mobaas
mcn_user_pwd  = mcn_12345_asdfkmg

mysql_exec = mysql --user=root --password="$(root_password)" --execute="$(1);";
create_database = $(call mysql_exec,CREATE DATABASE IF NOT EXISTS $(1))
drop_database = $(call mysql_exec,DROP DATABASE IF EXISTS $(1))

databases = bandwidth_predicted_database mobility_predicted_database mp_fetched_database bp_fetched_database mean_data_database

test_database = test_database
test_maas = test_maas

#Executables
executables = 1_start_test_maas.sh 2_start_mobaas.sh 3_start_test_mp_consumer.sh 4_start_test_bp_consumer.sh  install.sh remove.sh start_self_test.sh common.sh


#Install rules
default: create_databases pip_dependancies configure_executables install_flows_ts_module

pip:
	@ sudo apt-get install zabbix-agent
	@ sudo apt-get install python-dev --yes
	@ sudo apt-get install python-pip --yes
	@ sudo apt-get install git --yes

pip_dependancies: sql_python_driver python_numpy python_pykov

sql_python_driver: pip
	sudo pip install MySQL-python

python_numpy: pip
	sudo pip install numpy

python_pykov: pip python_numpy
	sudo apt-get install gfortran --yes
	sudo apt-get install liblapack-dev --yes
	sudo pip install scipy
	sudo pip install git+git://github.com/riccardoscalco/Pykov@master

sql_server: 
	@ echo "mysql-server-5.5 mysql-server/root_password password "$(root_password) | debconf-set-selections
	@ echo "mysql-server-5.5 mysql-server/root_password_again password "$(root_password) | debconf-set-selections
	@ sudo apt-get install mysql-server-5.5 --yes
	@ sudo apt-get install libmysqlclient-dev --yes

create_mcn_user: sql_server sql_python_driver
	$(call mysql_exec,CREATE USER '$(mcn_user_name)'@'localhost' IDENTIFIED BY '$(mcn_user_pwd)')
	$(call mysql_exec,GRANT ALL PRIVILEGES ON *.* TO '$(mcn_user_name)'@'localhost')

create_databases: sql_server sql_python_driver create_mcn_user
	$(foreach db, $(databases), $(call create_database, $(db)))

configure_executables:
	$(foreach executable, $(executables), sudo chmod 777 $(executable);)

install_flows_ts_module:
	cd ./flows_ts_module/; sudo make;

#Removal rules
 #SQL
remove_databases:
	$(foreach db, $(databases), $(call drop_database, $(db)))

remove_user: remove_databases
	$(call mysql_exec, DROP USER '$(mcn_user_name)'@'localhost')

remove_sql_server: remove_sql_python_driver remove_databases remove_user
	@ sudo apt-get purge mysql-server-5.5 --yes

remove_sql_python_driver: remove_user remove_databases
	@ sudo pip uninstall MySQL-python --yes

 #Pip and dependancies
remove_python_numpy: remove_python_pykov
	@ sudo pip uninstall numpy --yes

remove_python_pykov:
	@ sudo pip uninstall pykov --yes
	@ sudo pip uninstall scipy --yes
	@ sudo apt-get remove liblapack-dev --yes
	@ sudo apt-get remove gfortran --yes

remove_pip_dependancies: remove_sql_python_driver remove_python_numpy remove_python_pykov

remove_pip: remove_pip_dependancies
	@ sudo apt-get remove python-pip --yes
	@ sudo apt-get remove python-dev --yes
	@ sudo apt-get remove git --yes

 #Flows_ts module
remove_flows_ts_module:
	cd ./flows_ts_module/; sudo make remove;

remove: remove_pip remove_sql_server remove_flows_ts_module
	@ sudo apt-get autoremove --yes
	@ sudo rm -rf /var/lib/mysql


#Self Test rules
self_test: self_test_exec self_test_setup self_test_cleanup
	
self_test_setup:
	@ $(call create_database, $(test_database))

self_test_exec: self_test_setup
	@ export PYTHONPATH="$(shell pwd)"; \
	python ./mobaas/tests/run_tests.py
	
self_test_cleanup: self_test_setup self_test_exec self_test_cleanup_db	

self_test_cleanup_db:
	@ $(call drop_database, $(test_database))

#Demo rules
setup_demo:
	$(call create_database, $(test_maas))

teardown_demo:
	$(call drop_database, $(test_maas))
