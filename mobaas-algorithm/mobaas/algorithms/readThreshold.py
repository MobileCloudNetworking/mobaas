#!/usr/bin/pythonm

f = open('/home/ubuntu/mobaas/Groupeoutput/threshold_cell_users.txt','r')
print f.read()
f.close()

f = open('/home/ubuntu/mobaas/algorithms/stateText.txt','w')
f.write("1")
f.close()
