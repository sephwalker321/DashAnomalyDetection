"""============================================================================
Module to calculate various metrics reported in the dashboard it their suporting functions.

Contents:
- Features
- Fourier
- Alpha
- BOCPD
- PCA

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
import numpy as np
#For manipulating datetime format
from datetime import timedelta

import sys
import os
if sys.argv[0] == "JustRun.py":
	from EDFApp.codes import Misc
if sys.argv[0].split(os.sep)[-1] == "app.py":
	from codes import Misc

################################################################################################################
# Calc Stats Functions
################################################################################################################

######################
# Calc Stats: Features
######################

def CalcStats(data):
	''' Calculate some key statisitics from the data provided,
	data: A dataframe
	Return,
	Params: A dictionary of key statistics {"Mean", "STD", "Start", "End", "Rate", "RateUnit", "Duration", "Min", "Max"}
	'''
	Data_Mean = np.nanmean(data.values)
	Data_STD = np.nanstd(data.values, ddof=1)
	Data_StartDate = data.index[0]
	Data_EndDate = data.index[-1]
	if Data_StartDate != Data_EndDate:
		dT = abs(data.index[1]-data.index[0])
	
		Compare = abs(np.array([dT/timedelta(seconds=1),dT/timedelta(minutes=1),dT/timedelta(hours=1),dT/timedelta(days=1)])-1)
		Index = np.argwhere(Compare==min(Compare))[0][0]
		if Index == 0:
			Unit = "S"
			Data_SampleRate = (data.index[1]-data.index[0])/timedelta(seconds=1)
		elif Index == 1:
			Unit = "mins"
			Data_SampleRate = (data.index[1]-data.index[0])/timedelta(minutes=1)
		elif Index == 2:
			Unit = "hours"
			Data_SampleRate = (data.index[1]-data.index[0])/timedelta(hours=1)
		elif Index == 3:
			Unit = "days"
			Data_SampleRate = (data.index[1]-data.index[0])/timedelta(days=1)
	else:
		dT = 0
		Data_SampleRate = "N/A"
		Unit = ""
	Data_SampleDuration = (data.index[-1]-data.index[0])/timedelta(days=1) 
	Data_Min =  np.nanmin(data.values)
	Data_Max = np.nanmax(data.values)
	return {"Mean" : Misc.round_sig(Data_Mean,2),
			"STD" : Misc.round_sig(Data_STD,2),
			"Start" : Misc.unixTimeMillis(Data_StartDate),
			"End" : Misc.unixTimeMillis(Data_EndDate),
			"Rate" : Misc.round_sig(Data_SampleRate,2),
			"RateUnit" : Unit,
			"Duration" : Misc.round_sig(Data_SampleDuration,2),
			"Min" : Misc.round_sig(Data_Min,2),
			"Max" : Misc.round_sig(Data_Max,2) }

def CalcStatsEmpty():
	''' Dummy calculate some key statisitics,
	Return,
	Params: An empty dictionary of key statistics {"Mean", "STD", "Start", "End", "Rate", "RateUnit", "Duration", "Min", "Max"}
	'''
	return {"Mean" : "N/A",
		"STD" : "N/A",
		"Start" : "N/A",
		"End" : "N/A",
		"Rate" : "N/A",
		"RateUnit" : "",
		"Duration" : "N/A",
		"Min" : "N/A",
		"Max" : "N/A" }

######################
# Calc Stats: Fourier
######################

def CalcFourierStats(Fs, As, PPink, PPinkErrs):
	''' Calculate some key statisitics from frequency spectrum fit,
	Fs: frequencies
	As: Amplitude of frequency component
	PPink: Fitted Spectrum [A, Alpha]
	PPinkErr: Fitted Spectrum Errors [A, Alpha]
	Return,
	Params: A dictionary of key statistics {"Alpha", "A0", "AlphaErr", "A0Err", "FreqMin", "FreqMax"}
	'''
	Alpha = PPink[1]
	A0 = PPink[0]
	AlphaErr = PPinkErrs[1]
	A0Err = PPinkErrs[0]
	FreqMin = np.nanmin(Fs)
	FreqMax = np.nanmax(Fs)
	return { "Alpha" : Misc.round_sig(Alpha,2),
		"A0" : Misc.round_sig(A0,2),
		"AlphaErr" : Misc.round_sig(AlphaErr,2),
		"A0Err" : Misc.round_sig(A0Err,2),
		"FreqMin" : Misc.round_sig(FreqMin,2),
		"FreqMax" : Misc.round_sig(FreqMax,2)}

def CalcFourierStatsEmpty():
	''' Dummy calculate some key statisitics from frequency spectrum fit,
	Return,
	Params: An empty dictionary of key statistics {"Alpha", "A0", "AlphaErr", "A0Err", "FreqMin", "FreqMax"}
	'''
	return { "Alpha" : "N/A",
		"A0" : "N/A",
		"AlphaErr" : "N/A",
		"A0Err" : "N/A",
		"FreqMin" : "N/A",
		"FreqMax" : "N/A" }

######################
# Calc Stats: Alpha
######################

def CalcAlphaStats(Alphas):
	''' Calculate some key statisitics from the data provided,
	Alphas: A dataframe
	Return,
	Params: A dictionary of key statistics {"Min", "Max", "Mean", "STD"}
	'''
	Min = np.nanmin(Alphas.values)
	Max = np.nanmax(Alphas.values)
	Mean = np.nanmean(Alphas.values)
	STD = np.nanstd(Alphas.values, ddof=1)
	return { "Min" : Misc.round_sig(Min,2),
		"Max" : Misc.round_sig(Max,2),
		"Mean" : Misc.round_sig(Mean,2),
		"STD" : Misc.round_sig(STD,2)}

def CalcAlphaStatsEmpty():
	''' Dummy calculate some key statisitics from anaylsis,
	Return,
	Params: An empty dictionary of key statistics {"Min", "Max", "Mean", "STD"}
	'''
	return { "Min" : "N/A",
		"Max" : "N/A",
		"Mean" : "N/A",
		"STD" : "N/A"}

######################
# Calc Stats: BOCPD
######################

def CalcBOCPDStats(R_Max, tol):
	''' Calculate some key statisitics from the data provided,
	R_Max: Array of maximal propabilty sequences
	tol: BOCPD tol limit
	Return,
	Params: An empty dictionary of key statistics {"NoZeros", "NoOnes", "NoTwos", "MaxSeq", "MeanSeq", "tol"}
	'''
	values, counts = np.unique(R_Max, return_counts=True)
	if len(counts) > 2:
		NoZeros = float(counts[0]-1)
		NoOnes = float(counts[1])
		NoTwos = float(counts[2])
	elif len(counts) > 1:
		NoZeros = float(counts[0]-1)
		NoOnes = float(counts[1])
		NoTwos = 0.0	
	elif len(counts) > 0:
		NoZeros = float(counts[0]-1)
		NoOnes = 0.0
		NoTwos = 0.0
	elif len(counts) == 0:
		NoZeros = 0.0
		NoOnes = 0.0
		NoTwos = 0.0
	MaxSeq = float(np.nanmax(R_Max))
	MeanSeq = np.nanmean(R_Max)
	return { "NoZeros" : Misc.round_sig(NoZeros,2),
		"NoOnes" : Misc.round_sig(NoOnes,2),
		"NoTwos" : Misc.round_sig(NoTwos,2),
		"MaxSeq" : Misc.round_sig(MaxSeq,2),
		"MeanSeq" : Misc.round_sig(MeanSeq,2),
		"tol" : tol}

def CalcBOCPDStatsEmpty():
	''' Dummy calculate some key statisitics from anaylsis,
	Return,
	Params: An empty dictionary of key statistics {"NoZeros", "NoOnes", "NoTwos", "MaxSeq", "MeanSeq", "tol"}
	'''
	return { "NoZeros" : "N/A",
		"NoOnes" : "N/A",
		"NoTwos" : "N/A",
		"MaxSeq" : "N/A",
		"MeanSeq" : "N/A",
		"tol" : "N/A"}

######################
# Calc Stats: PCA
######################

def CalcPCAStats(Ts, Qs, NPCA, Vs, Regions):
	''' Dummy calculate some key statisitics from anaylsis,
	Ts: The t squared hotelling statistic,
	Qs: The Q resisduals statistic,
	NPCA: The dimensionality of the model used, 
	Vs: The fractional variance in each component over time
	Regions: The regions violating the limits.
	Return,
	Params: A dictionary of key statistics {"NRegions", "TsMean", "QsMean", "TsMax", "QsMax", "NPCA", "VarianceFracs"}
	'''
	NRegions = Regions.shape[0]
	TsMean = np.nanmean(Ts["Ts"].values)
	QsMean = np.nanmean(Qs["Qs"].values)
	TsMax = np.nanmax(Ts["Ts"].values)
	QsMax = np.nanmax(Qs["Qs"].values)
	VFracs = np.nanmean(Vs.values, axis=0)
	return { "NRegions" : NRegions,
		"TsMean" : Misc.round_sig(TsMean,2),
		"QsMean" : Misc.round_sig(QsMean,2),
		"TsMax" : Misc.round_sig(TsMax,2),
		"QsMax" : Misc.round_sig(QsMax,2),
		"NPCA" : NPCA,
		"VarianceFracs" : Misc.round_sig(sum(VFracs[:NPCA]),2) }

def CalcPCAStatsEmpty():
	''' Dummy calculate some key statisitics from anaylsis,
	Return,
	Params: An empty dictionary of key statistics {"NRegions", "TsMean", "QsMean", "TsMax", "QsMax", "NPCA", "VarianceFracs"
	'''
	return { "NRegions" : "N/A",
		"TsMean" : "N/A",
		"QsMean" : "N/A",
		"TsMax" : "N/A",
		"QsMax" : "N/A",
		"NPCA" : "N/A",
		"VarianceFracs" : "N/A"}


if __name__ == "__main__":
	print("Run as module") 
