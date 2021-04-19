"""============================================================================
Module of standard loading / saving and log checking functions

Contents:
- Loading functions
- Glob functions
- Log functions

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""

import numpy as np
import pandas as pd
# Get files in folder
import glob
import xlrd
import json

import os

################################################################################################################
# Data manipulation functions
################################################################################################################

######################
# Loading Functions JUSTRUN:
######################

def LoadDataSheets(DataDirectory, ColName, SheetNum, inter=True):
	'''Load data from the DataDirectory,
	DataDirectory: Folder of data to be loaded
	ColName: The name of the sheet to be loaded
	SheetNum: The sheet to be loaded
	inter: T/F if to interpolate values
	Return,
	DATA: Loaded dataframe'''
	#Values formated as strings to be removed
	na_values=['Under Range', 'Over Range', 'Set to Bad', "[-11059] No Good Data For Calculation", "No good data for summary calculation.", "Insufficient good data"]

	FileName = DataDirectory+os.sep+ColName+".xlsx"
	DATA = pd.read_excel(FileName,
		sheet_name="%s" % SheetNum,
		header=0,na_values=na_values,
		convert_float=False, index_col=0)

	if inter == True:
	#Interpolate nan values
		for ColName in DATA.columns:
			Miss = pd.to_numeric(DATA[ColName], errors='coerce').isnull() == True
			#Replace any string NaNs to numerical NaNs
			DATA[ColName] = pd.to_numeric(DATA[ColName], errors='coerce')
			#Replace NaNs with neighbouring value by interpolation
			DATA[ColName] = DATA[ColName].interpolate(method ='linear', limit_direction ='both',limit=100) 
	DATA = DATA[~DATA.index.duplicated(keep='first')]
	return DATA

def PCALOADSheets(Dir,Features,EventNum):
	''' Load individual files forming the dataframe for PCA
	Dir: Directory of data
	Features: List of file names
	EventNum: Sheetnumber
	Return,
	df: The loaded DataFrame
	'''
	for V_i in range(len(Features)):
		Var = Features[V_i] 
		if V_i == 0:
			df = LoadDataSheets(Dir, Var, EventNum).iloc[:, [0]] 
			df.columns = [Var]				
		else:
			df[Var] = LoadDataSheets(Dir, Var, EventNum).iloc[:, 0]

	#Drop anynans
	#df = df.dropna()
	df = df.replace([np.inf, -np.inf], np.nan)
	df = df.dropna()
	return df

######################
# Loading Functions App:
######################

def LoadData(DataDirectory, ColName, inter=True):
	'''Load data from the DataDirectory,
	DataDirectory: Folder of data to be loaded
	ColName: The name of the sheet to be loaded
	inter: T/F if to interpolate values
	Return,
	DATA: Loaded dataframe'''
	#Values formated as strings to be removed
	na_values=['Under Range', 'Over Range', 'Set to Bad', "[-11059] No Good Data For Calculation", "No good data for summary calculation.", "Insufficient good data"]

	FileName = DataDirectory+os.sep+ColName+".xlsx"
	DATA = pd.read_excel(FileName,
		header=0,na_values=na_values,
		convert_float=False, index_col=0)

	if inter == True:
		#Interpolate nan values
		for ColName in DATA.columns:
			Miss = pd.to_numeric(DATA[ColName], errors='coerce').isnull() == True
			#Replace any string NaNs to numerical NaNs
			DATA[ColName] = pd.to_numeric(DATA[ColName], errors='coerce')
			#Replace NaNs with neighbouring value by interpolation
			DATA[ColName] = DATA[ColName].interpolate(method ='linear', limit_direction ='both',limit=100) 
	return DATA

def PCALOAD(Dir,Features):
	''' Load individual files forming the dataframe for PCA
	Dir: Directory of data
	Features: List of file names
	Return,
	df: The loaded DataFrame
	'''
	for V_i in range(len(Features)):
		Var = Features[V_i] 
		if V_i == 0:
			df = LoadData(Dir, Var)
			df_V = df.iloc[:,[0]]
			df_E = df.iloc[:,[1]]
			df_V.columns = [Var]	
			df_E.columns = [Var]				
		else:
			df = LoadData(Dir, Var)
			df_V[Var] = df.iloc[:,[0]]
			df_E[Var] = df.iloc[:,[1]]
	#Drop anynans
	df_V = df_V.replace([np.inf, -np.inf], np.nan)
	df_V = df_V.dropna()
	#df_V = df_V.replace([np.nan], 0)
	df_E = df_E.replace([np.inf, -np.inf], np.nan)
	df_E = df_E.dropna()
	#df_E = df_E.replace([np.nan], 0)
	return df_V, df_E

######################
# Glob functions:
######################

def GlobDirectory(DataDirectory):
	'''Create list of files in DataDirectory,
	DataDirectory: Folder of data to be loaded
	Return,
	Files: List of files contained in DataDirectory'''
	Files = glob.glob(DataDirectory+os.sep+"*."+FileSuffix)
	FilesKeep = []
	for i in range(len(Files)):
		ith = Files[i].split(os.sep)[-1].split("."+FileSuffix)[0]
		if ith != "logs":
			FilesKeep.append(ith)
	FilesKeep.sort()
	return FilesKeep

def GlobEvents(DataDirectory, ColName):
	'''Get number of events (sheets) in file of DataDirectory,
	DataDirectory: Folder of data to be loaded,
	ColName: The name of the sheet to be loaded,
	Return,
	NEvents: Number of sheets == number of events recorded'''
	FileName = DataDirectory+os.sep+ColName+"."+FileSuffix
	File = pd.ExcelFile(FileName)
	return len(File.sheet_names)

######################
# Log functions:
######################

def write_json(data, filename):
	'''Write JSON to file.
	data: JSON
	FileName: JSON filename
	Return,
	1: If completes without error.
	'''
	with open(filename,'w') as f:
		json.dump(data, f, indent=4)
	return 1

def WriteCacheFile(FileName, data_i):
	'''Write cache file detailing a run with timestamps, feature details etc.
	FileName: JSON filename
	data_i: JSON dictionary to append / create.
	Return,
	1: If completes without error.
	'''
	Files = glob.glob(FileName)
	if FileName not in Files:
		data = {}
		data["Run_N"] = [data_i]
		
		with open(FileName,'w') as f:
			json.dump(data, f, indent=4)

	else:
		with open(FileName) as json_file:
			data = json.load(json_file)
			data["Run_N"].append(data_i)
	
	write_json(data, FileName) 
	return 1


def CheckExists(DataDirectory, CheckDirectory, FileName):
	'''Check if file exists and then if sheet exists.
	DataDirectory: Folder of raw data,
	CheckDirectory: Folder of processes data
	SheetNum: FileName to check,
	return,
	FileExists: T/F,
	'''
	if FileName in GlobDirectory(CheckDirectory):
		return True
	else:	
		return False

def CheckLog(DataDirectory, CheckDirectory):
	'''Check files for completion across anaylsis
	DataDirectory: Folder of raw data,
	CheckDirectory: Folder of processes data
	SheetNum: FileName to check,
	return,
	FileExists: T/F,
	Percentage: T and F counts in log
	'''
	Files = GlobDirectory(DataDirectory)
	FilesCheck = GlobDirectory(CheckDirectory)
	Tot = len(Files)
	if Tot == 0:
		return 0
	else:
		N = 0
		for File in Files:
			if File in FilesCheck:
				N+=1
			else:
				continue
		
		return 100*N/Tot
				
if __name__ == "__main__":
	print("Run as module") 
