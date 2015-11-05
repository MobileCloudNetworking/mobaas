'''
-this code calculates the transition probability for all user that have trace files, given a current time(12:44), current day(Monday) and transition time(20).
- the results save in 'IC output' folder and display in screen.
-this calculation repeated for every transition time, starting from current time
-for every repeting, a new file is created. 
-input command should be like '$ python ./mobaas/multi_user_prediction.py 0000 23:00 Monday 20'
'''
#!/usr/bin/pythonmmy
# -*- coding: utf-8 -*-
import pykov
import numpy
import random
import pylab
import collections
import sys
import os.path
from pylab import *
from array import *
import time
import timeit
import shutil
import pysparse
import pprint

start = timeit.default_timer()
##input the traced files in an array
def mp(user_id,current_time,current_day,transiant_num):

	# Dict to store all the individual results, to be returned at the end of the code
	result = {}

	## print current input time and dat
	print '********************************************************************************'
	print 'Current time is: ', current_time,  '  &   Currer day is : ' , current_day
	print '********************************************************************************'

	## set time and data using system time 
	Day = current_day

	if Day=='Saturday':
			current_day = 'sat'
	elif Day=='Sunday':
			current_day = 'sun'
	elif Day=='Monday':
			current_day = 'mon'
	elif Day=='Tuesday':
			current_day = 'tue'
	elif Day=='Wednesday':
			current_day = 'wed'
	elif Day=='Thursday':
			current_day = 'thu'
	elif Day=='Friday':
			current_day = 'fri'
	
	
	path_user = './mobaas/test_data/Trace_Files/'
	dirs = os.listdir( path_user)
	
	# remove the 'ICNoutput' and create a new one to save results
	shutil.rmtree('./mobaas/ICNoutput') 
	if not os.path.exists('./mobaas/ICNoutput'):
    		os.makedirs('./mobaas/ICNoutput')

	# start a while loop to calculate and save the results in 'ICNoutput' folder till time 24:00-transiant_num  		
	current_time_in_min = sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))
	#while (sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))<(1440-transiant_num)):
 	#stop prediction at 18:40, for the purpose of demo to limit the period of prediction
	while (sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))<(1130-transiant_num)):	

		#change current time to min, add ransiant_num to it, change to xx:yy format, put in Temp_time			
		current_time_in_min = sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))
		next_time_in_min = current_time_in_min + transiant_num
		Temp_time = '{:02d}:{:02d}'.format(*divmod(next_time_in_min, 60))
		
		#open and save the result in an new file
		f4 = open('./mobaas/ICNoutput/cellprobability_file_ICN_%s.txt' % Temp_time, 'w')
		f4 = open('./mobaas/ICNoutput/cellprobability_file_ICN_%s.txt' % Temp_time, 'a')
		f4.write('%s    %s  \n' % (Day, current_time))
		f4.write('%s  \n' % ('---------------------------------------------------'))
		f4.write('%s  \n' % ('user--current cell--next time--next cell--probability'))
		f4.write('%s  \n' % ('---------------------------------------------------'))
		for i in range(0, len(dirs)):
			user_id=int(dirs[i])
			##print 'Current user : ', user_id
		
			#count total number of files in each folder(based on user number of traced files are different)
			path = './mobaas/test_data/Trace_Files/''%d%s' % (user_id,'/Step_1')
			number_of_files_all_day = len([item for item in os.listdir(path) if os.path.isfile(os.path.join(path, item))]) #total number of files
			#print number_of_files_all_day
			total_input_file = number_of_files_all_day/7  #total input trace file for each day
			#print total_input_file 
			file_num = int(total_input_file*0.7 )   # 70% number of the input traced files for each week day for estimation 
			#print file_num 
			total_file_num=1*file_num  # number of total input traced files 
			array_of_traces=[]   # an empty array to input traced files as matrix for all dayes
			 
			## bades on the date read the trace files for specifie day
			##Saturdays
			if current_day == 'sat':
				sat_array_of_traces = [0]*file_num    # an empty array to input traced files as matrix for all Saturday
				for i in range(0, file_num):
					sat_trace_file=numpy.loadtxt('%s/Sat_%d.dat' % (path, i))    #read the traced files(Saturday)
					size=len(sat_trace_file)       # size of trace files step
					sat_array_of_traces[i] = sat_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = sat_array_of_traces
			 	#print 'Current day is :' , current_day
			##Sundays
			elif current_day == 'sun':
				sun_array_of_traces = [0]*file_num    # an empty array to input traced files as matrix for all Sundays
				for i in range(0, file_num):
					sun_trace_file=numpy.loadtxt('%s/Sun_%d.dat' % (path, i))    #read the traced files(Sundays)
					size=len(sun_trace_file)       # size of trace files step
					sun_array_of_traces[i] = sun_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = sun_array_of_traces
				#print 'Current day =' , current_day
			##Mondays
			elif current_day == 'mon':
				mon_array_of_traces = [0]*file_num    # an empty array to input traced files as matrix for all Monday
				for i in range(0, file_num):
					mon_trace_file=numpy.loadtxt('%s/Mon_%d.dat' % (path, i))    #read the traced files(Monday)
					size=len(mon_trace_file)       # size of trace files step
					mon_array_of_traces[i] = mon_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = mon_array_of_traces
			 	#print 'Current day =' , current_day
			##Tusedays
			elif current_day == 'tue':
				tue_array_of_traces = [0]*file_num    # an empty array to input traced files as matrix for all Tuseday
				for i in range(0, file_num):
					tue_trace_file=numpy.loadtxt('%s/Tue_%d.dat' % (path, i))    #read the traced files(Tuseday)
					size=len(tue_trace_file)       # size of trace files step
					tue_array_of_traces[i] = tue_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = tue_array_of_traces
			 	#print 'Current day =', current_day
			##Wednesdays
			elif current_day == 'wed':
				wed_array_of_traces = [0]*file_num    # an empty array to input traced files as matrix for all Wednesday
				for i in range(0, file_num):
					wed_trace_file=numpy.loadtxt('%s/Wed_%d.dat' % (path, i))    #read the traced files(Wednesday)
					size=len(wed_trace_file)       # size of trace files step
					wed_array_of_traces[i] =wed_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = wed_array_of_traces
			 	#print 'Current day =' , current_day
			##Thursdays
			elif current_day == 'thu':
				thu_array_of_traces = [0]*file_num    # an empty array to input traced files as matrix for all Thursday
				for i in range(0, file_num):
					thu_trace_file=numpy.loadtxt('%s/Thu_%d.dat' % (path, i))    #read the traced files(Thursday)
					size=len(thu_trace_file)       # size of trace files step
					thu_array_of_traces[i] =thu_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = thu_array_of_traces
			 	#print 'Current day =' , current_day
			##Fraidays
			elif current_day == 'fri':
				fri_array_of_traces = [0]*file_num    # an empty array to input traced files as for all Friday
				for i in range(0, file_num):
					fri_trace_file=numpy.loadtxt('%s/Fri_%d.dat' % (path, i))    #read the traced files(Friday)
					size=len(fri_trace_file)       # size of trace files step
					fri_array_of_traces[i] = fri_trace_file  # input each traces fiel in the array 
				#array_of_traces.extend(sat_array_of_traces)
				array_of_traces = fri_array_of_traces
			 	#print 'Current day =' , current_day

			#*********************************************************************************************************************
			##count number of visited cell
			arry_of_temp_cell=[0]*total_file_num    #an array to put the cell ID in each step 
			arry_of_number_cell=[0]*size      #an array to count the number of visited cell ID 
			arry_of_number_cell_copy=[0]*size      #an array to count the number of visited cell ID 
			for j in range(0, size):
				for i in range(0, total_file_num):
					arry_of_temp_cell[i]=array_of_traces[i][j][1]
					arry_of_number_cell[j]=[[x,arry_of_temp_cell.count(x)] for x in set(arry_of_temp_cell)]
					arry_of_temp_cell[i]=array_of_traces[i][j][1]
					arry_of_number_cell_copy[j]=[[x,arry_of_temp_cell.count(x)] for x in set(arry_of_temp_cell)]

			##count percentage of visited cell
			arry_of_percentage_cell=arry_of_number_cell_copy #an array to calculate the percentage for each visited cell
			for j in range(0, size):
				sum_cell=0.
				for n in range(0,len(arry_of_percentage_cell[j])):
					sum_cell += arry_of_percentage_cell[j][n][1]   #calculate all visited cell 
				for n in range(0,len(arry_of_percentage_cell[j])):
					arry_of_percentage_cell[j][n][1]=arry_of_percentage_cell[j][n][1]/sum_cell   #calculate the percentage for each visited cell 

			##make an array to save time,percentage and cell ID
			arry_of_time_percentage_cell=arry_of_percentage_cell #an array to save [time_cellID, percentage]
			for j in range(0, ):
				for n in range(0,len(arry_of_percentage_cell[j])):
					arry_of_time_percentage_cell[j][n][0]=['%d%s%d' %(array_of_traces[0][j][0],'-',arry_of_percentage_cell[j][n][0])]

			#*********************************************************************************************************************
			#open file to save the state file (state file is calculated from this file that has non zero transient probability)
			f1 = open('./mobaas/ICNoutput/statefile_ICN.txt', 'w')
			f1 = open('./mobaas/ICNoutput/statefile_ICN.txt', 'a')
			##calculate the percentage of going from once cell to other cell in each step 
			#matrix_of_number_next_cell_percentage=[0]*t
			for j in range(0,size-2):
				for n in range(0,len(arry_of_number_cell[j])):  #an array which has the number of visited cell in each step
					#print (n)
					arry_of_temp_next_cell=[]
					arry_of_number_next_cell=[]
					arry_of_number_next_cell_copy=[]
					temp=arry_of_number_cell[j][n][0]       # temp get each of the visited cell

					for i in range(0, total_file_num):
						if array_of_traces[i][j][1]==temp:
							#an array to save visited cell in the next step
							arry_of_temp_next_cell.append(array_of_traces[i][j+1][1])
							#an array which has the number of visited cell in the next step				
							arry_of_number_next_cell=[[x,arry_of_temp_next_cell.count(x)] for x in set(arry_of_temp_next_cell)]
							#make a copy					
							arry_of_number_next_cell_copy=[[x,arry_of_temp_next_cell.count(x)] for x in set(arry_of_temp_next_cell)]
							arry_of_number_next_cell_percentage=arry_of_number_next_cell_copy
							#calculate the percentage of going to the next cell					
							sum_next_cell=0.
							for n in range(0,len(arry_of_number_next_cell_percentage)):
								sum_next_cell += arry_of_number_next_cell_percentage[n][1] 
								#print(sum_next_cell)
							for n in range(0,len(arry_of_number_next_cell_percentage)):
								arry_of_number_next_cell_percentage[n][1]=arry_of_number_next_cell_percentage[n][1]/sum_next_cell
							#print(sum_next_cell)
					#save the the transient probability in state file 		
					for m in range(0,len(arry_of_number_next_cell_percentage)):
						f1.write('%s%d' % ('c', array_of_traces[0][j][0]))
						f1.write('%s%d   ' % ('_',temp))
						f1.write('%s%d' % ('c', array_of_traces[0][j+1][0]))
						f1.write('%s%d   %.3f \n' % ('_',arry_of_number_next_cell_percentage[m][0],arry_of_number_next_cell_percentage[m][1]))

			f1.close()		

			#********************************************************************************************************************
		    ## change hh:mm to time step (e.g, 06:21-->381 )
			current_time_setp = sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))
			
			##calculate the transient probability
			state_mat = pykov.readmat('./mobaas/ICNoutput/statefile_ICN.txt')
					
			## save list of cell in current time
			current_cell_list = []
			for i in range(0,len(state_mat)):
				temp_time = int(state_mat.keys()[i][0][1:state_mat.keys()[i][0].index('_')])
				if temp_time == current_time_setp:
					#print '-------------'
					temp_cell=int(state_mat.keys()[i][0][state_mat.keys()[i][0].index('_')+1:])
					if temp_cell !=0:			
						current_cell_list.append(temp_cell)
			
			## consider only one possibility form all currrent cell
			## chech if 'current_cell_list' is not empty!
			if current_cell_list:
				current_cell = current_cell_list[0]
				#print 'current cell : ',  current_cell

				## make time step and cell as 'c381_5384 '
				current_time_cell = ('%s%d%s%d' % ('c', current_time_setp ,'_',current_cell ))
				#print  current_time_cell

				#initial_state = pykov.Vector(c614_39184   = 1)
				initial_state = pykov.Vector([(current_time_cell, 1)])
				next_cell_probability = state_mat.pow(initial_state, transiant_num)
				result[(user_id, current_cell, Temp_time)] = []
				for prob_key in next_cell_probability.keys():
					next_cell = prob_key[prob_key.index('_') + 1:]
					if next_cell != '0':
						result[(user_id, current_cell, Temp_time)] += [(next_cell, "%.4f" % next_cell_probability[prob_key])]


				f3 = open('./mobaas/ICNoutput/state_mat_ICN.txt', 'w')
				for i in range(0,len(state_mat.values())):
					f3.write('%s      %f \n' % (state_mat.keys()[i], state_mat.values()[i]))

				f3.close()

				#the result file
				x=[]
				cell_name=[]
				y=[]

	
				for i in range(0,len(next_cell_probability.values())):
					x.append(i+1)
					cell_name.append(next_cell_probability.keys()[i])
					y.append(next_cell_probability.values()[i])
					temp_next_cell = next_cell_probability.keys()[i]
					if  temp_next_cell[temp_next_cell.index('_') + 1:] != '0':
						f4.write('%d     ' % (user_id))
						f4.write('%d     ' % (current_cell))
						f4.write('%s  %s  %f \n' % ('{:02d}:{:02d}'.format(*divmod(int(temp_next_cell[1:temp_next_cell.index('_')]), 60)), temp_next_cell[temp_next_cell.index('_') + 1:], next_cell_probability.values()[i]) )

				f4.write('%s  \n' % ('   '))

		f4.close()
		
		# put the (current_time)=(current_time+transiant_num)	
		current_time=Temp_time
		###print  current_time
		print "result:"
		pprint.pprint(result)
		return result
	   

#*********************************************************************************************************************

def main():
	if len(sys.argv) != 5:

		print 'This script needs 4 commandline arguments !!'
		print 'Input user ID (0000) time (10:14) day(Monday) next time (10) !!'
	else:
		mp(int(sys.argv[1]),sys.argv[2],sys.argv[3],int(sys.argv[4])) 
	stop = timeit.default_timer()
	print 'Execution time is : ',  (stop - start) , 'Second'
	return 0

if __name__ == "__main__":
	main()





















