#!/bin/bash

n=1
 
# continue until $n equals 5
while [ $n -le 10 ]
do
	python  ./mobaas/algorithms/group_mobility_prediction.py
	n=$(( n+1 ))	 # increments $n
done

   

