/*
 * flows-ts-v3.cc
 *
 * DESCRIPTION:
 *  This program reads a ASC-II file containing flows records generated by
 *  yaf/yafscii. The flow information is divided in timeseries and the load
 *  in bytes is equally distributed throughout the flow. This software can be
 *  used for creating a timeline and reading a timeline in different timescales.
 *
 * INPUT:
 *  The input file must have seven columns separated by one blank space. All
 *  columns are mandatory and must follow the specific order:
 *    <start_time> <end_time> <duration> <saddr> <daddr> <packets> <bytes>
 *
 * OUTPUT:
 *  See function printLine().
 *
 * Ricardo de O. Schmidt
 * November 2, 2011
 *
 * Design and Analysis of Communication Systems (DACS)
 * University of Twente (UT)
 * The Netherlands
 *
 */
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/param.h>
#include <sys/stat.h>
#include <unistd.h>

#include <map>
#include <string>
#include <cstring>
#include <iostream>
#include <fstream>
#include <math.h>

using namespace std;

/* 
 * timeline map; the key is the timestamp in milliseconds
 *
 */
typedef map<long int, double> tl_t;

/* struct to store flow information that is read from the file */
struct line_t {
	long smls; // Start milliseconds 
	long emls; // End milliseconds
	long dur; // Duration in seconds
	char* saddr;
	char* daddr;
  	long pkts;
	long bytes;
	long ssec; // Start seconds
	long esec; // End seconds
};

/**
 * int procLine()
 *
 * This function separates the python tuple into the line_t
 * so all python values are converted to C values.
 * Python tuple should contain:
 * <start_time> :: LongInt 
 * <end_time> :: LongInt
 * <saddr> :: String
 * <daddr> :: String
 * <packets> :: Int 
 * <bytes> :: Int
 * 
 */
static int procLine(line_t* line, PyObject* flow_data_tuple) {
	PyObject* start_time_py, *end_time_py, *saddr_py, *daddr_py, *packets_py, *bytes_py;

	/* start milliseconds */
	start_time_py = PyTuple_GetItem(flow_data_tuple, 0);
	line->smls = PyInt_AsLong(start_time_py);

	/* end milliseconds */
	end_time_py = PyTuple_GetItem(flow_data_tuple, 1);
	line->emls = PyInt_AsLong(end_time_py);

	/* source address */
	saddr_py = PyTuple_GetItem(flow_data_tuple, 2);
	line->saddr = PyString_AsString(saddr_py);

	/* destination address */
	daddr_py = PyTuple_GetItem(flow_data_tuple, 3);
	line->daddr = PyString_AsString(daddr_py);

	/* Number of packets */
	packets_py = PyTuple_GetItem(flow_data_tuple, 4);
	line->pkts = PyInt_AsLong(packets_py);

	/* Number of bytes */
	bytes_py = PyTuple_GetItem(flow_data_tuple, 5);
	line->bytes = PyInt_AsLong(bytes_py);

	line->ssec = line->smls / 1000;
	line->esec = line->emls / 1000;

	/* duration */
	line->dur = line->esec - line->ssec;

	return 0;
}

/**
 * int addToTimeline()
 *
 * This function adds the flow values from struct line_t to the timeline.
 *
 */
static int addToTimeline(line_t* line_p, tl_t* tl_bytes_p) {
	tl_t& tl_bytes = *tl_bytes_p;
	line_t line = *line_p;

  int flow_bytes; // flow total bytes
  long int actual_flow_dur; // flow duration in seconds
  long int flow_dur_ml; // flow duration in milliseconds
	long int first_bin_ml, last_bin_ml;
	double first_bin_perc_time, last_bin_perc_time, inter_bin_perc_time;
	double first_bin_bytes, last_bin_bytes, inter_bin_bytes;
	long int cur_sec;

  /* iterator to navigate through the timeline map */
  tl_t::iterator tl_it;

  /* flow total duration in milliseconds and total bytes */
  actual_flow_dur = line.dur;
  flow_bytes = line.bytes;


	/* if the flow has less than 1 second, just add the total bytes to the respective second */
	if (actual_flow_dur == 0) {
		tl_it = tl_bytes.find(line.ssec);
		if (tl_it == tl_bytes.end())
			tl_bytes.insert(pair<long int, double>(line.ssec, flow_bytes));
		else
			tl_bytes[line.ssec] += flow_bytes;
	}
	/* if the flow is equal or longer than 1 second, and spreads over several seconds, calculate the share */
	else {
		// total duration in milliseconds
		flow_dur_ml = line.emls - line.smls;

		/* calculate the share of the first second */
		first_bin_ml = 1000 - (line.smls - line.ssec * 1000);
		first_bin_perc_time = (double) first_bin_ml / flow_dur_ml;
		first_bin_bytes = flow_bytes * first_bin_perc_time;
		tl_it = tl_bytes.find(line.ssec);
		if (tl_it == tl_bytes.end())
			tl_bytes.insert(pair<long int, double>(line.ssec, first_bin_bytes));
		else
			tl_bytes[line.ssec] += first_bin_bytes;

		/* calculate the share of the intermediate seconds if any */
		cur_sec = line.ssec + 1;
		while (cur_sec < line.esec) {
			inter_bin_perc_time = (double) 1000 / flow_dur_ml;
			inter_bin_bytes = flow_bytes * inter_bin_perc_time;
			tl_it = tl_bytes.find(cur_sec);
			if (tl_it == tl_bytes.end())
				tl_bytes.insert(pair<long int, double>(cur_sec, inter_bin_bytes));
			else
				tl_bytes[cur_sec] += inter_bin_bytes;
			
			cur_sec++;
		}

		/* calculate the share of the last second */
		last_bin_ml = line.emls - line.esec * 1000;
		last_bin_perc_time = (double) last_bin_ml / flow_dur_ml;
		last_bin_bytes = flow_bytes * last_bin_perc_time;
		tl_it = tl_bytes.find(line.esec);
		if (tl_it == tl_bytes.end())
			tl_bytes.insert(pair<long int, double>(line.esec, last_bin_bytes));
		else
			tl_bytes[line.esec] += last_bin_bytes;

	}

	return 0;
}

/**
 * int fillTimeGaps()
 *
 * This function fills all time gaps in the timeline, considering a milliseconds
 * timescale.
 *
 *  TODO - this function can be joined with fillTimeGaps, so that only one loop
 *  will be executed through the timeline.
 *
 */
static int fillTimeGaps(tl_t* tl_bytes_p) {
	tl_t& tl_bytes = *tl_bytes_p;
	long int prev_ml; // previous millisecond
	long int cur_ml; // current millisecond

	/* iterator to navigate through the timeline map */
	tl_t::iterator tl_it;

	/* control variables initialization */
	tl_it = tl_bytes.begin();
	cur_ml = tl_it->first;
	prev_ml = cur_ml - 1;

	/* loop for passing through all entries in the timeline map */
	for (tl_it = tl_bytes.begin(); tl_it != tl_bytes.end(); tl_it++) {
		cur_ml = (*tl_it).first;
		if (cur_ml - prev_ml != 1) {
			prev_ml++;
			while (prev_ml < cur_ml) {
				tl_bytes.insert(pair<long int, double>(prev_ml, 0));
				prev_ml++;
			}
		}
		prev_ml = cur_ml;
	}

	return 0;
}

static void fill_time_line_python_list(PyObject* timeline_result, tl_t* tl_bytes_p) {
	tl_t& tl_bytes = *tl_bytes_p;

	for(tl_t::iterator tl_it = tl_bytes.begin(); tl_it != tl_bytes.end(); tl_it++) {
		PyObject* time_throughput_tuple = PyTuple_New(2);
		PyObject* time = PyInt_FromLong(tl_it->first);
		PyObject* throughput = PyFloat_FromDouble(tl_it->second);

		PyTuple_SetItem(time_throughput_tuple, 0, time);
		PyTuple_SetItem(time_throughput_tuple, 1, throughput);

		PyList_Append(timeline_result, time_throughput_tuple);
	}

}

static void clear_line(line_t* line_p) {
	line_p->smls = 0;
	line_p->emls = 0;
	line_p->dur = 0;
	line_p->saddr = NULL;
	line_p->daddr = NULL;
	line_p->pkts = 0;
	line_p->bytes = 0;
	line_p->ssec = 0;
	line_p->esec = 0;
}

static PyObject* flows_ts_process_flow_data(PyObject *self, PyObject *args) {
	tl_t tl_bytes;
	tl_bytes.clear();
	line_t line;

	PyObject* result;
	PyObject* list_of_flow_data;
	PyArg_ParseTuple(args, "O!", &PyList_Type, &list_of_flow_data);

	Py_ssize_t list_size = PyList_Size(list_of_flow_data);
	Py_ssize_t i = 0;
	PyObject* flow_data_tuple;	

	while(i < list_size) {
		flow_data_tuple = PyList_GetItem(list_of_flow_data, i);
		clear_line(&line);
		procLine(&line, flow_data_tuple); // split line info
		addToTimeline(&line, &tl_bytes); // add info to the timeline
		i++;
	}


	if (fillTimeGaps(&tl_bytes) > 0) {
		result = Py_None;
	} else {
		PyObject* timeline_result = PyList_New(0);

		fill_time_line_python_list(timeline_result, &tl_bytes);//Convert map to Python list object
		result = timeline_result;
	}

	return result;
}

static PyMethodDef Flows_tsMethods[] = {
	{"process_flow_data", flows_ts_process_flow_data, METH_VARARGS, "Creates a flow timeline based on the inputlist."},
	{NULL, NULL, 0, NULL} /* Sentinel */
};

PyMODINIT_FUNC initflows_ts(void) {
	(void) Py_InitModule("flows_ts", Flows_tsMethods);
}