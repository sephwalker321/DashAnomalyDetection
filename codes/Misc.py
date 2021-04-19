"""============================================================================
Module of miscelaneous functions used throughout.

Contents:
- Fitted Parameters Return
- Useful
- Time Functions
- Window Functions
- ErrorCalcs
- String Key Search

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
import scipy
import numpy as np
import pandas as pd
import time
import os

import scipy
from sklearn import decomposition
from sklearn.preprocessing import StandardScaler

#For manipulating datetime format
from datetime import datetime
from datetime import timedelta

################################################################################################################
# Functions:
################################################################################################################

#######################
# Fitted Parameters Return
#######################

def GetOptimzed(PCA_FittedParams, Type, StringSearch, Metric, Vars):
	PowList = IndexPattern("BF604", Vars)
	TherList = IndexPattern("RP209", Vars)
	GagList = IndexPattern("GA201", Vars)
	if len(PowList) > 0 and len(TherList) > 0 and len(GagList) > 0:
		StringSearch = "CGO"
	if PCA_FittedParams[Type] == None:
		PCA_NPCA = PCA_FittedParams["None"]["NPCA"]
		PCA_AlphaLim = PCA_FittedParams["None"]["AlphaLim"]
		PCA_Thresh = PCA_FittedParams["None"]["Thresh"]
	elif StringSearch in PCA_FittedParams[Type].keys():
		PCA_NPCA = PCA_FittedParams[Type][StringSearch][Metric]["NPCA"]
		PCA_AlphaLim = PCA_FittedParams[Type][StringSearch][Metric]["AlphaLim"]
		PCA_Thresh = PCA_FittedParams[Type][StringSearch][Metric]["Thresh"]
	else:
		PCA_NPCA = PCA_FittedParams["None"]["NPCA"]
		PCA_AlphaLim = PCA_FittedParams["None"]["AlphaLim"]
		PCA_Thresh = PCA_FittedParams["None"]["Thresh"]
	return PCA_NPCA, PCA_AlphaLim, PCA_Thresh

#######################
# Useful
#######################
		
def round_sig(x, sig=2):
	''' Rounds to sig fig.
	x: variable to be rounded
	sig: Num sig figs
	Return
	rounded: The rounded number
	'''
	if isinstance(x, (float, int)):
		if np.isfinite(x) and x != 0:
			return round(x, sig-int(np.floor(np.log10(abs(x))))-1)

		else:
			return x
	else:
			return x
	
#######################
# Time Functions
#######################

def unixTimeMillis(dt):
	''' Convert datetime to unix timestamp.
	dt : datetime format,
	Return,
	Unix : The unix time stamp'''
	return int(dt.timestamp())
	#return time.mktime(dt.timetuple())

def unixToDatetime(unix):
	''' Convert unix timestamp to datetime. 
	unix: unix time format,
	Return,
	timestamp : The time stamp in datatime format'''
	return pd.to_datetime(unix,unit='s')

def getMarksDates(start, end, dates, NPoints=5):
	''' Returns the marks for labeling.
	start: First date in list,
	end: Last date in list,
	dates: List of all dates with plotted point,
	NPoints: How many marks to include,
	Return,
	result: The tick marks for the plots'''
	result = {}
	Nth = np.linspace(0,len(dates),NPoints,dtype = int, endpoint=True)
	Nth[-1] -= 1
	for i, date in enumerate(dates):
		if i in list(Nth):
			# Append value to dict
			result[unixTimeMillis(date)] = str(date.strftime('%d/%m/%Y'))
	return result

def getDateTimeFromString(string):
	''' Convert datetime string to datetime object using a list of formats to decode
	string: datatime string
	Return,
	t: datetime object.
	'''
	fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
	for fmt in fmts:
		try:
			t = datetime.strptime(string, fmt)
			break
		except ValueError as err:
			pass
	return t

#######################
# Window Functions
#######################

def WindowSize(Rate, RateUnit, Duration, NDuration):
	''' Return how many datepoints in data for a given hourly rate to get the required duration
	Rate: The sample rate,
	RateUnit: The units of the rate
	Duration: string [second, minute, hour, day, week] duration multiple
	NDuration: N times the Duration eg. 2 * weeks
	Return,
	N: Int number of datapoints to be sampled
	'''
	if Duration in ["S","second", "seconds"]:
		dt = NDuration*timedelta(seconds=1)
	if Duration in ["mins","minute", "minutes"]:
		dt = NDuration*timedelta(minutes=1)
	if Duration  in ["hours","hour"]:
		dt = NDuration*timedelta(hours=1)
	if Duration in ["days","day"]:
		dt = NDuration*timedelta(days=1)
	if Duration in ["weeks","week"]:
		dt = NDuration*timedelta(weeks=1)
	if RateUnit in ["S","second", "seconds"]:
		return int(dt / (timedelta(seconds=1)*Rate))
	if RateUnit in ["mins","minute", "minutes"]:
		return int(dt / (timedelta(minutes=1)*Rate))
	if RateUnit  in ["hours","hour"]:
		return int(dt / (timedelta(hours=1)*Rate))
	if RateUnit in ["days","day"]:
		return int(dt / (timedelta(days=1)*Rate))
	if RateUnit in ["weeks","week"]:
		return int(dt / (timedelta(weeks=1)*Rate))

def CalcUnits(Rate, RateUnit):
	''' Return units into years
	Rate: The sample rate,
	RateUnit: The units of the rate
	Duration: string [second, minute, hour, day, week] duration multiple
	Return,
	units: rate in years
	'''
	if RateUnit in ["S","second", "seconds"]:
		return ((3600*24*365)/Rate)
	if RateUnit in ["mins","minute", "minutes"]:
		return ((60*24*365)/Rate)
	if RateUnit in ["hours","hour"]:
		return ((1*24*365)/Rate)
	if RateUnit in ["days","day"]:
		return ((365)/Rate)
	if RateUnit in ["week","weeks"]:
		return ((52)/Rate)

def timedeltaOneUnit(Rate,RateUnit):
	''' Return a timedelta element of one sample
	Rate: The sample rate,
	RateUnit: The units of the rate
	Return,
	timedelta: A timedelta of one sample
	'''
	if RateUnit in ["S","second", "seconds"]:
		return Rate*timedelta(seconds=1)
	if RateUnit in ["mins","minute", "minutes"]:
		return Rate*timedelta(minutes=1)
	if RateUnit in ["hours","hour"]:
		return Rate*timedelta(hours=1)
	if RateUnit in ["days","day"]:
		return Rate*timedelta(days=1)
	if RateUnit in ["weeks","week"]:
		return Rate*timedelta(weeks=1)
	
#######################
# ErrorCalcs
#######################

def errCalculation(data, RateUnit, Mean=False):
	''' The error estimation on the raw data,
	data: np.array of data
	RateUnit: The units of the rate,
	Mean: 0 if return array, 1 if return mean to get scalar value.
	Return,
	errs: np. array of estimated errors
	'''
	#Assuming data is sampled at rate of once per second. Typical of most.
	#How many measurments?
	if RateUnit in ["S","second", "seconds"]:
		N = 1
	if RateUnit in ["mins","minute", "minutes"]:
		N = 60
	if RateUnit in ["hours","hour"]:
		N = 3600
	if RateUnit in ["days","day"]:
		N = 3600*24	
	if Mean == False:
		return data["Error"].values #/ np.sqrt(N)
	if Mean == True:
		return np.nanmean(data["Error"].values )#/ np.sqrt(N))

#######################
# String Key Search
#######################

def IndexPattern(Key, List):
	''' Functions to pull out strings matching to "key" in list, List.
	Key: String key to search for,
	List: List to look through for strings with substring "Key",
	Return,
	L: List of items in List with Key in strings'''
	if Key not in [None]:
		return [s for s in List if Key in s]
	else:
		return []

def PatternsList(StrSearch, Files):
	'''TODO
	'''
	StrSep = StrSearch.split(",")+StrSearch.split(" ,")+StrSearch.split(", ")
	KeySelected=[]
	for i in range(len(StrSep)):
		if StrSep[i] not in ["", " "]:
			KeySelected += IndexPattern(StrSep[i], Files)
	KeySelected = sorted(list(set(KeySelected)))
	return KeySelected
			
if __name__ == "__main__":
	print("Run as module") 