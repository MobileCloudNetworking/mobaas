#!/usr/bin/pythonmy
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
from collections import Counter
from collections import OrderedDict
from pylab import *
from array import *
import time
from numpy import * 
from pylab import *
from array import *
import time
import timeit
import shutil

start = timeit.default_timer()

path_user = './mobaas/test_data/Trace_Files/'
dirs = os.listdir(path_user)
#print len(dirs)

#def mp(user_id, current_day, current_time):
#def mp(current_day, current_time):
#def mp(transiant_num, thr_user_number):
def mp():
	transiant_num=30
	thr_user_number=5
	#get transiant_num and thr_user_number from input
	## set time and data using system time 
	Day = datetime.date.today().strftime("%A")
	Time = time.strftime("%H:%M")
	current_time = Time
	
	# start a while loop to calculate and save the results in 'ICNoutput' folder till time 24:00-transiant_num  		
	current_time_in_min = sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))
	##$print  current_time_in_min 
	while (sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))<(1440-transiant_num)):
		##$print '	'
		##$print '**********Group Mobility Prediction is runing *****************'
		##$print 'transiant time is : ', transiant_num 
		##$print 'thresh old for user number is :', thr_user_number	
		##$print 'Current date is: ', Day ,  '  &   Currer time is : ', Time
		#print 'Currer day is : ', +Day ' & Current time is: ', +Time   
		##$print '****************************************************************'
		##$print "------The Calculation of the Group Mobility Prediction based on the Trajectory Trace Files------" 
		#print 'Current time :' +Time 
		#print 'Current date :'	+Day



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

		shutil.rmtree('./mobaas/Groupeoutput') 
		if not os.path.exists('./mobaas/Groupeoutput'):
				os.makedirs('./mobaas/Groupeoutput')

		all_users_start_move_cell_prob=[] # a matrix to save all_users_start_move_cell_prob 
		f8=open('./mobaas/Groupeoutput/all_users_start_move_cell_prob.txt','a')
		for file in dirs:
			user_id = int(file)
			#print '...................' 
			##$print 'User ID :' , user_id
			##$print '...................' 

			#transiant_num =20  # after how many minutes!
			path = './mobaas/test_data/Trace_Files/''%d%s' % (user_id,'/Step_1')
			number_of_files_all_day = len([item for item in os.listdir(path) if os.path.isfile(os.path.join(path, item))]) 			#total number of files
			#print number_of_files_all_day
			total_input_file = number_of_files_all_day/7  #total input trace file for each day
			#print total_input_file 
			file_num = int(total_input_file*0.8 )   # 80% number of the input traced files for each week day for estimation 
			#print file_num 
			total_file_num=1*file_num  # number of total input traced files 
			array_of_traces=[]   # an empty array to input traced files as matrix for all dayes
			#print " " 
			#print " " 
			#print "------The Calculation of the Probabilities based on the Trajectory Trace Files -------" 

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
			f1 = open('./mobaas/Groupeoutput/statefile.txt', 'w')
			f1 = open('./mobaas/Groupeoutput/statefile.txt', 'a')
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

			#*********************************************************************************************************************
			##calculate the transient probability
			state_mat = pykov.readmat('./mobaas/Groupeoutput/statefile.txt')
			#print len(state_mat)
			#print state_mat.keys()

			## change hh:mm to time step (e.g, 06:21-->381 )
			current_time_setp = sum(int(x) * 60 ** i for i,x in enumerate(reversed(current_time.split(':'))))
			#current_time_setp = current_time_setp - transiant_num  # set the start time "transiant_num" ago to from current time to start M.C
			current_time_setp = current_time_setp # set the start time "transiant_num" ago to from current time to start M.C
			#print current_time_setp
			#print len(state_mat)	
	
			#Clear the cellprobabilityfile.txt for new calculation
			f4 = open('./mobaas/Groupeoutput/cellprobabilityfile.txt', 'w')
			f4.close()

			#check the "current_time_setp - transiant_num" in state_mat to find the valid cell on that time
			for i in range(0,len(state_mat)):
				if  int(state_mat.keys()[i][0][1:state_mat.keys()[i][0].index('_')]) == current_time_setp:
					if int(state_mat.keys()[i][0][state_mat.keys()[i][0].index('_') + 1:])!=0:
						##$print '**************************************************************************************'
						#print state_mat.keys()[i][0]
						current_time_cell = state_mat.keys()[i][0]
						#verey important point here is that now "current_cell" is not the cell at current time, 
						#here it shows the cell that user was ther at "current_time_setp -transiant_num " 	
						current_cell =int(state_mat.keys()[i][0][state_mat.keys()[i][0].index('_') + 1:])  
						#print  current_time_cell
						#print  current_cell
						## make time step and cell as 'c381_5384 '
						initial_state = pykov.Vector([(current_time_cell, 1)])
						#print initial_state
						next_cell_probability = state_mat.pow(initial_state, transiant_num)

						f3 = open('./mobaas/Groupeoutput/state_mat.txt', 'w')
						for i in range(0,len(state_mat.values())):
							f3.write('%s      %f \n' % (state_mat.keys()[i], state_mat.values()[i]))

						f3.close()

						#the result file
						x=[]
						cell_name=[]
						y=[]

						#return next_cell_probability
						## print the caclulation of probability in the screen and save it in the "cellprobabilityfile.txt" file, this file only show the probability of moving fron start cell to current cell
						##$print "Starting time for estimation = "'{:02d}:{:02d}'.format(*divmod(current_time_setp, 60)), "  ,   User is in cell = ", (current_cell)  
						##$print "......................................................................................" 
						#f4 = open('./mypath/groupprediction/cellprobabilityfile.txt', 'w')
						f4 = open('./mobaas/Groupeoutput/cellprobabilityfile.txt', 'a')
						for i in range(0,len(next_cell_probability.values())):
							x.append(i+1)
							cell_name.append(next_cell_probability.keys()[i])
							y.append(next_cell_probability.values()[i])
						#	f4.write('%s      %f \n' % (next_cell_probability.keys()[i],next_cell_probability.values()[i]))
							temp_next_cell = next_cell_probability.keys()[i]
							#f4.write('%s  %s  %s  %f \n' % (current_cell, '{:02d}:{:02d}'.format(*divmod(int(temp_next_cell[1:temp_next_cell.index('_')]), 60)), temp_next_cell[temp_next_cell.index('_') + 1:], next_cell_probability.values()[i]) )
							#f4.write('%s  %s  %f \n' % (current_cell, temp_next_cell[temp_next_cell.index('_') + 1:], next_cell_probability.values()[i]) )
							#f4.write('\n------------------')
							if  temp_next_cell[temp_next_cell.index('_') + 1:] != '0':
								f4.write('%s  %s  %f \n' % (current_cell, temp_next_cell[temp_next_cell.index('_') + 1:], next_cell_probability.values()[i]) )
								##$print 'Next Time = ' '{:02d}:{:02d}'.format(*divmod(int(temp_next_cell[1:temp_next_cell.index('_')]), 60)),'  ,  Current Cell = ', temp_next_cell[temp_next_cell.index('_') + 1:],'  ,  The Probability = ', next_cell_probability.values()[i]
							##$elif  temp_next_cell[temp_next_cell.index('_') + 1:] == '0':
								##$print 'Next Time  = ' '{:02d}:{:02d}'.format(*divmod(int(temp_next_cell[1:temp_next_cell.index('_')]), 60)),'  ,  Current Cell = ', temp_next_cell[temp_next_cell.index('_') + 1:],'(Not trace data)','  ,  The Probability = ', next_cell_probability.values()[i]
						#f4.write('--------\n')	

						f4.close()

			# load cellprobabilityfile in a matrix
			prob_mat = numpy.loadtxt('./mobaas/Groupeoutput/cellprobabilityfile.txt')
			#print 'original prob_mat : ',prob_mat
			#print'...................' 
	
			number_of_element_prob_mat = numpy.count_nonzero(prob_mat)
			#print 'number of element in original prob_mat', number_of_element_prob_mat
			#print'...................' 
			#find unique row in  prob_mat
			def unique_rows(a):
					a = numpy.ascontiguousarray(a)
					unique_a = numpy.unique(a.view([('', a.dtype)]*a.shape[1]))
					return unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))
			
			if  number_of_element_prob_mat > 3:
				prob_mat = unique_rows(prob_mat)
				#print 'unic prob_mat',prob_mat
				#print'...................' 

			number_of_element_prob_mat = numpy.count_nonzero(prob_mat)
			#print 'number of element in unic prob_mat', number_of_element_prob_mat		
			# check if prob_mat dose not have only one raw(it has three elements), inorder to find unic raw in it		
			if  number_of_element_prob_mat == 3:
				#print 'number of raw in prob_mat', raw_of_prob_mat 		
				new_prob_mat_1 = numpy.append(prob_mat, 0)
	 			new_prob_mat_2 = numpy.append(new_prob_mat_1, 0)
				#print 'now prob_mat', new_prob_mat_2				
				prob_mat_extend = new_prob_mat_2
				#new = numpy.append(prob_mat, 0)
				#new1 = numpy.append(new, 0)
				#raw_of_punique_rows_prob_mat = len(unique_rows_prob_mat)
				#print 'number of raw in raw_of_punique', raw_of_punique_rows_prob_mat
				#prob_mat_extend= np.c_[ unique_rows_prob_mat, 0, 0 ]	
				#unique_rows_prob_mat.extend([0, 0])
				#C =[0]*2
				#prob_mat_extend= np.c_[ unique_rows_prob_mat, np.zeros(1), np.zeros(1) ]	
				#print prob_mat_extend	
				#print len(prob_mat_extend)
				size_of_prob_mat_extend=1
				#print  size_of_prob_mat_extend 

			elif number_of_element_prob_mat !=3:
				#print 'number of raw in prob_mat', raw_of_prob_mat 		
				unique_rows_prob_mat = unique_rows(prob_mat)
				raw_of_punique_rows_prob_mat = len(unique_rows_prob_mat)
				#print 'number of raw in raw_of_punique', raw_of_punique_rows_prob_mat		
				prob_mat_extend= np.c_[ unique_rows_prob_mat, np.zeros(raw_of_punique_rows_prob_mat), np.zeros(raw_of_punique_rows_prob_mat) ]	
				#print prob_mat_extend
				size_of_prob_mat_extend=len(prob_mat_extend)
				#print  size_of_prob_mat_extend 

			# calculate the probability of starting from one specific cell
			count_start_cell_numb= Counter(unique_rows_prob_mat[:,0])
			#print 'count_start_cell_numb',  count_start_cell_numb
			uniq_start_cell_numb= 1. * len(unique_rows_prob_mat[:,0])
			#print 'uniq_start_cell_numb', uniq_start_cell_numb
			count_start_cell_perc = numpy.zeros(shape=(len(count_start_cell_numb),2))
			for i in range(0,len(count_start_cell_numb)):
				count_start_cell_perc[i,0]= count_start_cell_numb.keys()[i]
				count_start_cell_perc[i,1]= count_start_cell_numb.values()[i]/uniq_start_cell_numb
				#print count_start_cell_perc[i,0]
				#print count_start_cell_perc[i,1]

			#print count_start_cell_perc 
	
			for i in range(0,len(count_start_cell_perc)):
				temp_cell = count_start_cell_perc[i,0]
				temp_prob = count_start_cell_perc[i,1]          #probability that user was in the start cell
				#for j in range(0,len(prob_mat_extend[:,0])):
				if size_of_prob_mat_extend==1:
					#print  'in size 1 :', size_of_prob_mat_extend 
					#print 'prob_mat_extend =', prob_mat_extend
					#print 'prob_mat_extend[0]=', prob_mat_extend[2]
					#for j in range(0,size_of_prob_mat_extend):
					if prob_mat_extend[0]== temp_cell:
						prob_mat_extend[3]=temp_prob  #probability that user was in the start cell
						prob_mat_extend[4]=prob_mat_extend[3]* prob_mat_extend[2] #probability that user was in the start cell and move to the current cell
				else:
					#print  'in size more than 1:', size_of_prob_mat_extend 
					for j in range(0,size_of_prob_mat_extend):
						if prob_mat_extend[j,0]== temp_cell:
							prob_mat_extend[j,3]=temp_prob  #probability that user was in the start cell
							prob_mat_extend[j,4]=prob_mat_extend[j,3]* prob_mat_extend[j,2] #probability that user was in the start cell and move to the current cell
					
	
			#find unique row in  prob_mat_extend
			def unique_rows(a):
					a = numpy.ascontiguousarray(a)
					unique_a = numpy.unique(a.view([('', a.dtype)]*a.shape[1]))
					return unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))
	
			if size_of_prob_mat_extend!=1:		
				unique_rows_prob_mat_extend = unique_rows(prob_mat_extend)
				#useID_add_prob_mat_extend = prob_mat_extend
				useID_add_prob_mat_extend = unique_rows_prob_mat_extend 
				useID_add_prob_mat_extend = np.insert(useID_add_prob_mat_extend, 0, values= user_id, axis=1) 
				##numpy.savetxt('./mobaas/Groupeoutput/users_startcells_movecell_probability_%d.txt' % (user_id), useID_add_prob_mat_extend ,fmt='%.4f')
				numpy.savetxt(f8, useID_add_prob_mat_extend,fmt='%.4f')


			if size_of_prob_mat_extend==1:		
				unique_rows_prob_mat_extend = prob_mat_extend
				useID_add_prob_mat_extend = unique_rows_prob_mat_extend 
				useID_add_prob_mat_extend = np.insert(useID_add_prob_mat_extend, 0, user_id) 
				#useID_add_prob_mat_extend = useID_add_prob_mat_extend.T 
				##numpy.savetxt('./mobaas/Groupeoutput/users_startcells_movecell_probability_%d.txt' % (user_id), useID_add_prob_mat_extend[None] ,fmt='%.4f')
				numpy.savetxt(f8, useID_add_prob_mat_extend[None] ,fmt='%.4f')
				#np.savetxt(f,a)
		f8.close()			
			## in this matrix: the rows are : userID-start cell-visited cell-pobability to move to visited cell(P1)-pobalility that user was in start cell(P2)-P1*P2
			#numpy.savetxt('./mypath/groupprediction/Groupeoutput/users_startcells_movecell_probability_%d.txt' % (user_id), useID_add_prob_mat_extend ,fmt='%.4f')
	
	#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

	#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
		all_users_start_move_cell_prob = numpy.loadtxt('./mobaas/Groupeoutput/all_users_start_move_cell_prob.txt')
		#all_users_start_move_cell_prob is sorted based on row 2 (move cell) to find all users that move to 'move cell'
		sorted_all_users_start_move_cell_prob = all_users_start_move_cell_prob[all_users_start_move_cell_prob[:,2].argsort()]
	
		numpy.savetxt('./mobaas/Groupeoutput/sorted_all_users_start_move_cell_prob.txt', sorted_all_users_start_move_cell_prob  ,fmt='%.4f')


	#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
		# count how many number of users(with unic ID) are moved to 'move cell'
		count_user_in_move_cell= Counter(sorted_all_users_start_move_cell_prob[:,2])
		for i in range(0,len(count_user_in_move_cell)):
			temp_mat=sorted_all_users_start_move_cell_prob[numpy.where(sorted_all_users_start_move_cell_prob[:,2] == count_user_in_move_cell.keys()[i])]
			#print 'temp_mat',temp_mat[0,2]
			unic_user=Counter(temp_mat[:,0])
			unic_user_number=len(unic_user)
			#print 'unic_user', unic_user_number
			count_user_in_move_cell[temp_mat[0,2]]= unic_user_number
			#print 'count_user_in_move_cell.values()[i]', count_user_in_move_cell.values()[i]

		#print 'count_user_in_move_cell second', count_user_in_move_cell
	#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	
		# make another matrix to save the probabilites of users(for all users P1*P2)
		count_user_in_move_cell_extend = numpy.zeros(shape=(len(count_user_in_move_cell),4))
		for i in range(0,len(count_user_in_move_cell)):
			count_user_in_move_cell_extend[i,0]= count_user_in_move_cell.keys()[i]
			count_user_in_move_cell_extend[i,1]= count_user_in_move_cell.values()[i]
			#print 'number is user is : ' count_user_in_move_cell.values()[i]
	
		# sort the 'count_user_in_move_cell_extend' based on number of users	
		sorted_count_user_in_move_cell_extend =count_user_in_move_cell_extend[count_user_in_move_cell_extend[:,1].argsort()]
		#print 'sorted_count_user_in_move_cell_extend :' , sorted_count_user_in_move_cell_extend
		Temp_time='{:02d}:{:02d}'.format(*divmod(int(temp_next_cell[1:temp_next_cell.index('_')]), 60))
		##$print ' '		
		##$print '******** Notification******'
		##$print 'It is estimated at time (',Temp_time,') number of users in following cell will be more than defined threshold!'	

		numpy.savetxt('./mobaas/Groupeoutput/sorted_count_user_in_move_cell_extend.txt', sorted_count_user_in_move_cell_extend ,fmt='%.4f')

		f9 = open('./mobaas/Groupeoutput/threshold_cell_users.txt', 'w')
		f9 = open('./mobaas/Groupeoutput/threshold_cell_users.txt', 'a')
		for i in range(0,len(sorted_count_user_in_move_cell_extend)):
			if sorted_count_user_in_move_cell_extend[i,1] > thr_user_number:
				##$print 'In cell (', sorted_count_user_in_move_cell_extend[i,0], ') --> ', sorted_count_user_in_move_cell_extend[i,1] , 'users'
				f9.write('%s %s %s \n' % (Temp_time, sorted_count_user_in_move_cell_extend[i,0], sorted_count_user_in_move_cell_extend[i,1]))
	
		f9.close()		
	#####################

		# list for time, cell, number of users	
		threshold_cell_users = [line.strip() for line in open('./mobaas/Groupeoutput/threshold_cell_users.txt')]
		print threshold_cell_users 

	####################
		    
		for i in range(0,len(sorted_count_user_in_move_cell_extend)):
			temp_cell=sorted_count_user_in_move_cell_extend[i,0]
			#print temp_cell
			temp_prob_1=1.
			temp_prob_2=1.
			n=0.
			for j in range(0,len(sorted_all_users_start_move_cell_prob)):
				if temp_cell == sorted_all_users_start_move_cell_prob[j,2]:
					n=n+1
					temp_prob_1=temp_prob_1*sorted_all_users_start_move_cell_prob[j,5]+0.0000001

				#if temp_cell != sorted_all_users_start_move_cell_prob[j,2]:
				#	n=n+1
				#	temp_prob_2=temp_prob_2*(1-sorted_all_users_start_move_cell_prob[j,5])
			#print n	
			#print 'temp_prob_1 =' , temp_prob_1
			#print 'temp_prob_2 =' , temp_prob_2
			sorted_count_user_in_move_cell_extend[i,2]=(temp_prob_1*temp_prob_2)*100
			#print '(temp_prob_1*temp_prob_2)*100 = x=', (temp_prob_1*temp_prob_2)*100
			#sorted_count_user_in_move_cell_extend[i,3]=math.log10(temp_prob_1*temp_prob_2)
			sorted_count_user_in_move_cell_extend[i,3]=log10(temp_prob_1*temp_prob_2)

	
		numpy.savetxt('./mobaas/Groupeoutput/sorted_count_user_in_move_cell_extend.txt', sorted_count_user_in_move_cell_extend ,fmt='%.4f')


		'''
		#print 'sorted_count_user_in_move_cell_extend', sorted_count_user_in_move_cell_extend


		#Plot the cell number, numbe of user, probability  
		m = list(range(1, len(sorted_count_user_in_move_cell_extend)+1))
		fig = plt.figure()
		ax = plt.subplot(311)
		#plt.title('Cell ID, Numbe of user',fontsize = 4)
		plt.plot(m, sorted_count_user_in_move_cell_extend[:,1],'g:>')
		plt.ylabel('Numbe of user',fontsize = 4)
		plt.xlabel('Cell ID',fontsize = 4)
		plt.xticks(m, sorted_count_user_in_move_cell_extend[:,0], rotation='vertical' ,fontsize = 1)
		#ax.yaxis.grid(True)
		#ax.xaxis.grid(True)

		ax = plt.subplot(312)
		#plt.title('Cell ID,Probability',fontsize = 4)
		plt.plot(m, sorted_count_user_in_move_cell_extend[:,2],'r:*')
		plt.ylabel('Probability',fontsize = 4)
		plt.xlabel('Cell ID',fontsize = 4)
		plt.xticks(m, sorted_count_user_in_move_cell_extend[:,0], rotation='vertical',fontsize = 1)
		#ax.yaxis.grid(True)
		#ax.xaxis.grid(True)


		ax = plt.subplot(313)
		#plt.title('Cell ID, Log(10) of Probability',fontsize = 4)
		plt.plot(m, sorted_count_user_in_move_cell_extend[:,3],'b:^')
		plt.ylabel('Log(10) of Probability',fontsize = 4)
		plt.xlabel('Cell ID',fontsize = 4)
		plt.xticks(m, sorted_count_user_in_move_cell_extend[:,0], rotation='vertical',fontsize = 1)
		#ax.yaxis.grid(True)
		#ax.xaxis.grid(True)

		plt.savefig('./mobaas/Groupeoutput/sorted_count_user_in_move_cell_extend.pdf')   
		plt.close()
		'''

#*********************************************************************************************************************
def main():
	if len(sys.argv) != 1:
		print 'This script needs 4 commandline arguments !!'
		print 'Input user ID (6001), the day(wed), time (10:14), cell ID(39184) and next time (1) !!'
	else:
		#mp(int(sys.argv[1]),int(sys.argv[2])) 
		mp() 
		#mp() 
	stop = timeit.default_timer()
	print ''
	print '>>>>>>>>>>> Execution time is : ',  (stop - start) , 'Second'
	return 0




#if __name__ == "__main__":
print 'it works'
#	main()
