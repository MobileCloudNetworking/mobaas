#!/bin/bash

sudo make setup_demo
source ./common.sh

env | grep PYTHONPATH

python ./mobaas/demo_programmes/test_supplier.py

sudo make teardown_demo
