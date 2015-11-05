#!/bin/bash
echo "Script started monitoring the intermediary file"
file="/home/ubuntu/mobaas/algorithms/stateText.txt"
while true
do
	state=$(cat "$file")
	if [ "$state" == "1" ]; then
		echo "0" > $file
		pId=$(python "/home/ubuntu/mobaas/algorithms/group_mobility_prediction.py")
	else
		sleep 1
	fi
done
