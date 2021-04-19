"""============================================================================
The default hyper-parameters of the various tools used in the dashboard. 

Contents:
- Dashboard settings
- Anaylsis setting

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
#######################
# Dashboard settings
#######################

### Graphing ### 
# Error scaling on graphs * float
DefaultErrSize = 1                       #1
### String Search ###
# Defualt string search value "*, *, ..." string
DefaultFeature = ""
### Alpha / Raw ###
DefaultDataType = "Raw"
### Rescale ###
DefaultRescale = "None" 
## Metric ### F1 or Acc
DefaultMetric = "F1"

### BOCPD Hyperparameters ###
# Max sequence length for plotting / saving
BOCPD_MaxSeqLength = (24*7)*4              #(24*7)*4

### Excel settings ###
#Default Excel file extension "" string
FileSuffix = "xlsx"                     #"xlsx"

### Cached Files ###
# Save matplotlib figures 0/1 int
SaveFigs = 0                            #0
# Save cache files 0/1 int
SaveCache = 1                           #1


#######################
# Anaylsis setting. USE CAUTION.
#######################

### General Window parameters ###
#Ensure sample rate of data suitably small such that there's around ~100 points in a window. E.g a "day" window with a sample rate of every 10 minutes has 144 datapoints. 
#Window unit string from ["seconds", "mintues", "hours", "days", "weeks"]. 
WindowUnit = "week"                        #week
#Size of window in units above. * int
WindowN = 1                                #1

### Alpha Hyperparameters ###
#The minimum frequecy used in power spectrum fit. * float
Alpha_MinFreq = 0                          #0

### BOCPD Hyperparameters ###
# Drop off tolerance for long tails * float
BOCPD_tol = 1e-10                          #1e-10
# Rough expected CP rate in arbitary units * float
BOCPD_haz = 1/(200)                        #1/200
# Error scaling for datapoint errors * float
BOCPD_errsScale = 1                        #2

### PCA Hyperparameters ###
#Set by RETUNING...
PCA_FittedParams = { 
		"Raw": None,
		"Alpha": None,
		"BOCPD": None,
		"None" : {"NPCA" : 1, "AlphaLim" : 1e-2, "Thresh" : -1}, 	
}
### Rates Hyperparameters ###
Rolling_WindowUnit = "week"
Rolling_Window = 1
