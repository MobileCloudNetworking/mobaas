#!/bin/bash
source ./common.sh
python ./mobaas/database_connections/setup_databases.py
python ./mobaas/frontend.py &
python ./mobaas/webservice.py > /var/log/webservice.log 2>&1
python ./mobaas/database_connections/clear_databases.py
