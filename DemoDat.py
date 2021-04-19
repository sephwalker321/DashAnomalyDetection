"""============================================================================
Create sample dummy datasets to play out of box

Contents: 
- main
- SinData
- Distort
- Make Features
- Make All

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""

#Pandas for data import and management
import pandas as pd
import numpy as np

#For manipulating datetime format
from datetime import datetime
from datetime import timedelta

import sys, getopt
import os
import time

#Global variables
DirDemo = "data"+os.sep+"DemoData"
DirRaw = "data"+os.sep+"RawData"

def main(argv):
	''' Take inputs from command line,
	argv: Command line input,
	Return,
	RunSim: If to run demo simulated updates
	TSleep: Duration between updates in seconds
	dT: The interval between data simulated
	'''
	#Defualt parameters
	RunSim=False
	TSleep=60*5
	dT="h" 
	try:
		opts, args = getopt.getopt(argv,"RT:d:",["Run=","TSleep=","dT="])
	except getopt.GetoptError:
		print('python DemoDat.py -R -T <int> -d <s/m/h>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('python DemoDat.py -R -T <int> -d <s/m/h>')
			sys.exit()
		elif opt in ("-R"):
			RunSim = True
		elif opt in ("-T", "--TSleep"):
			TSleep = arg
		elif opt in ("-d", "--dT"):
			dT = arg
	return TSleep, RunSim, dT
  

def SinData(xs, T, A):
	''' Return sin function A sin(t),
	xs: ts ,
	T: Period of occilation ,
	A: Amplitude,
	Return,
	Ys: The evaluated function
	'''
	return A*np.sin(xs*2*np.pi/(T))

def Distort(Y, Type, N):
	''' Distortions to data.
	Y: Y values time series [],
	Type: One of ["None", "delta", "EndChange"]
	N: len(Y[:])
	Return,
	Y: Altered Y time series
	'''
	if Type == "None":
		#No changes
		return Y, []

	if Type == "delta":
		#Two regions of data peturbed by multiplier 
		indexA = np.random.randint(int(N*0.1),int(N*0.9))
		indexB = np.random.randint(int(N*0.5),int(N*0.9))
		for Yi in range(len(Y)):
			Y[Yi][indexA-12:indexA+12] *= 2
			Y[Yi][indexB-12:indexB+12] *= 2
			faults = [indexA, indexB]

	if Type == "EndChange":
		#End of data transformed
		index = np.random.randint(int(N*0.1),N)
		for Yi in range(len(Y)):
			Y[Yi][index:] += np.mean(Y[Yi][index:]) + np.random.rand(N-index)
			faults = [index]
	return Y, faults

def MakeFeatures(Xs, N, units):
	''' Produce three "feature" time series,
	Xs: ts,
	N: len(Xs),
	units: Conversion from hours
	Return
	Ys: Three sets of time series in list [Ys,Ys,Ys, Ys]
	Names: Names of series ["A","B","C", "D"]
	'''
	Ys = []
	Errors = []
	#Feature 1: Daily occilation
	T = 24 * units
	A = 10
	NA = 1
	Ys.append(SinData(Xs,T,A)+np.random.normal(size=N)*0.3*NA*A)
	Errors.append(np.zeros(N)+NA*A/2)
	#Feature 2: Daily + Weekly occilation
	T = 24 * units
	A = 10
	NA = 1
	Ys.append(SinData(Xs,T,A)+SinData(Xs,T*7,A)+np.random.normal(size=N)*0.3*NA*A)
	Errors.append(np.zeros(N)+NA*A/2)
	#Feature 3: twice Daily + Daily + yearly occilation
	T = 24 * units
	ASmall = 10
	ABig = 100
	NA = .3
	Ys.append(SinData(Xs,T,A)+SinData(Xs,T*0.5,A)+SinData(Xs,T*365,ABig)+np.random.normal(size=N)*NA*ASmall+np.random.normal(size=N)*NA*ABig)
	Errors.append(np.zeros(N)+np.sqrt((NA*ASmall)**2.0 + 0.1*(NA*ABig)**2.0))
	#Feature 4: Noisy trendline
	T = 24 * units
	A = 10
	NA = .3
	Ys.append(0.001*Xs+T+np.random.normal(size=N)*0.3*NA*A)
	Errors.append(np.zeros(N)+(NA*A)/2)
	return Ys, Errors
	

def MakeAll(RunSim, dT, TotalDuration, SliceDuration, TSleep):
	''' Create three time series and save to Demo folder
	RunSim: If to run demo simulated updates
	dT: The interval between data simulated
	TotalDuration: Required number of time points,
	SliceDuration: Required number of time points in each slice,
	TSleep: Duration between updates on files,
	Return,
	'''
	if dT == "s":
		dtDatetime = timedelta(seconds=1)
		units = 3600
	elif dT == "m":
		dtDatetime = timedelta(minutes=1)
		units = 60
	elif dT == "h":
		dtDatetime = timedelta(hours=1)
		units = 1
	elif dT == "d":
		dtDatetime = timedelta(days=1)
		units = 1/24
	
	Xs = np.arange(0,TotalDuration,1)
	indexTime = Xs*dtDatetime + datetime(2018,1,1,0,0) 
	Types = ["None", "delta", "EndChange"]
	Names = ["A", "B", "C", "D"]

	Distorts = []
	faults = []
	_, Errors = MakeFeatures(Xs, TotalDuration, units)
	for Di in range(len(Types)):
		D = Distort(MakeFeatures(Xs, TotalDuration, units)[0], Types[Di], TotalDuration)
		Distorts.append(D[0])
		faults.append(indexTime[D[1]])

	modeB="w"
	for Fi in range(len(Names)):
	#Loop over features A, B and C
		modeA="w"
		Name = Names[Fi]
		for Di in range(len(Types)):
			#Saved FULL set to Demo for comparison
			df = pd.DataFrame(
				data = { "%s_%s" % (Name, Types[Di]): Distorts[Di][Fi], "Error" : Errors[Fi]},
				index = indexTime 
			)
			writer = pd.ExcelWriter("%s" % (DirDemo)+os.sep+"%s_%s.xlsx" % ( Name, Types[Di]), mode=modeA)
			df.to_excel(writer)
			writer.save()


		df = pd.DataFrame(
				data = { "Faults": faults},
			)
		writer = pd.ExcelWriter("%s" % (DirDemo)+os.sep+"Faults.xlsx", mode=modeB)
		df.to_excel(writer)
		writer.save()


	print("Created demo data complete in %s" % (DirDemo) )
	if RunSim == True:
		FileRWtime = 0.2
		TTotal = (TSleep+FileRWtime)*(TotalDuration-SliceDuration)
		m, s = divmod(TTotal, 60)
		h, m = divmod(m, 60)
		print("Now simulating updates every %s seconds into %s" % (TSleep, DirRaw) )
		print("Time to completion: %02dh:%02dm:%02ds" % (h,m,s) )
		print(" ")

		for Ti in range(SliceDuration, TotalDuration):
		#Simulated periodic updates to the data
			if Ti > SliceDuration:
				#Inforced wait
				time.sleep(TSleep) 
			print(indexTime[Ti-SliceDuration],indexTime[Ti])
			for Fi in range(len(Names)):
				mode="w"
				Name = Names[Fi]
				for Di in range(len(Types)):
					#Saved FULL set to Demo for comparison
					df = pd.DataFrame(
						data = { "%s_%s" % (Name, Types[Di]): Distorts[Di][Fi] , "Error" : Errors[Fi]},
						index = indexTime
					)

					writer = pd.ExcelWriter("%s" % (DirRaw)+os.sep+"%s_%s.xlsx" % ( Name, Types[Di]), mode=mode)
					df.iloc[Ti-SliceDuration:Ti].to_excel(writer)
					writer.save()
					
	return 1
	
		


if __name__ == "__main__":
	TSleep, RunSim, dT = main(sys.argv[1:])
	SliceDuration = 24*7*1
	TotalDuration = 24*7*2
	MakeAll(RunSim, dT, TotalDuration, SliceDuration, TSleep)
