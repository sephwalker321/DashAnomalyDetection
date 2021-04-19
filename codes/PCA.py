"""============================================================================
Module containing relevent PCA tools

Contents:
- PCA Confidence limit funcs
- RegionSlicer On Confidence
- PCA

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
import numpy as np
import pandas as pd

import scipy
from sklearn import decomposition
from sklearn.preprocessing import StandardScaler
from datetime import timedelta

import os
import sys
if sys.argv[0] == "JustRun.py":
	from EDFApp.codes import Misc
if sys.argv[0].split(os.sep)[-1] == "app.py":
	from codes import Misc

Rolling_WindowUnit = "week"
Rolling_Window = 1

################################################################################################################
# Functions:
################################################################################################################

#######################
# Useful
#######################

def Gaussian(Mean, SD, x): 
	''' Gaussian function;
	Mean: Gaussian center
	SD: Standard Deviation
	x: array or value to evaluate'''
	return np.exp(-0.5*((x-Mean)/SD)**2.0)/(SD*np.sqrt(2*np.pi))

def PValue(Mean,SD,Xmin,Xmax):
	''' Return PVaule from integrating guassian between limits;
	Mean: Gaussian center,
	SD: Standard Deviation,
	Xmin: Integral lower limit,
	Xmax: Integral lower limit'''
	return scipy.integrate.quad(lambda x: Gaussian(Mean,SD,x), Xmin,Xmax)

#######################
# PCA Confidence limit funcs
#######################

def QLimFunc(Zs, theta):
	''' Q resisidual statistic for PCA model of desired confidence;
	Zs: The Z score required,
	thetas: [lambda, lambda^2, lambda^3] where lambda is the variance contained for each PCA component,
	Return
	Q: The Q value for this Z score and given model.
	'''
	h0 = 1 - ((2*theta[0]*theta[2])/(3*theta[1]**2))
	return theta[0]* (1 + (Zs*h0*np.sqrt(2*theta[1])/theta[0])+(theta[1]*h0*(h0-1)/theta[0]**2))**(1/h0)

def QLimInv(Qs, theta):
	''' Confidence for a given Q resisidual statistic for PCA model;
	Qs: The Q value for given model
	thetas: [lambda, lambda^2, lambda^3] where lambda is the variance contained for each PCA component,
	Return
	Z: Z score,
	Pval: The P value,
	'''
	if np.sum(theta) != 0:
		h0 = 1 - ((2*theta[0]*theta[2])/(3*theta[1]**2))
		A = (Qs/theta[0])**(h0) - 1
		B = (theta[1]*h0*(h0-1))/theta[0]
		C = 1/(h0*np.sqrt(2*theta[1]))
		Z = C*(A*theta[0] - B)
		if isinstance(Qs, (list, tuple, np.ndarray)):
			Ps = np.zeros(len(Qs))
			for i in range(len(Qs)):
				Ps[i] = PValue(0,1,Z[i] ,np.inf)[0]
			return Z, Ps
		else:
			return Z, PValue(0,1,Z ,np.inf)[0]
	else:
		if isinstance(Qs, (list, tuple, np.ndarray)):
			Ps = np.ones(len(Qs))
			Z = np.zeros(len(Qs)) + -np.inf
			return Z, Ps
		else:
			return -np.inf,1

def TLimFunc(Zs,NPCA,n):
	'''t squared hotteling statistic for PCA model of desired confidence;
	Zs: The Z score required,
	NPCA: The dimensionality of the model used,
	n: The number of datapoints in the training of model,
	Return
	t: The tsq value for this Z score and given model.
	'''
	if isinstance(Zs, (list, tuple, np.ndarray)):
		alpha = np.zeros(len(Zs))
		for i in range(len(Zs)):
			alpha[i] = PValue(0,1,-np.inf ,Zs[i])[0]
	else:
		alpha = PValue(0,1,-np.inf ,Zs)[0]
	Val = scipy.stats.f.ppf(q=alpha, dfn=NPCA, dfd=n-NPCA)* ((( n*n - 1 )*NPCA) / (n*(n-NPCA)))
	return Val

def TLimInv(Val, NPCA,n):
	''' Confidence for a given tsq resisidual statistic for PCA model;
	Val: The tsq value for given model
	NPCA: The dimensionality of the model used,
	n: The number of datapoints in the training of model,
	Return
	Pval: The P value,
	'''
	Perc = scipy.stats.f.cdf(x=Val/ ((( n*n - 1 )*NPCA) / (n*(n-NPCA))), dfn=NPCA, dfd=n-NPCA)
	return 1-Perc

#######################
# RegionSlicer On Confidence
#######################

def GetRegionsRate(df1, df2, dtMeasure, AlphaLim, NPCA, TestCol):
	RatesAlpha = []
	
	for i in AlphaLim:
		RegionsAll, RegionsSpecific, RatesAll, RatesSpecific =  PCA.PCARegionsCollect(df1, df2, dtMeasure, PCA_AlphaLim, NPCA, TestCol)
		RatesAlpha.append(RatesAll)

	return RatesAlpha

def GetRegions(df1, df2, index, dtMeasure, AlphaLim, TestCol = 0, NDur=0):
	''' Take two series and check for True and False concurance.
	df1: Panda Series one
	df2: Panda Series two
	index: Array of df1, df2 index
	dtMeasure: A timedelta object of distance between measurments
	AlphaLim: Required Pval threshold
	NDur: Minumum number of flag points.
	Return,
	Highlighted: A dataframe of regions which contain the True values across both series.
	dfRates: A dataframe of an estimator of the flag rates over time.
	'''
	
	RollingWinSize = int(Misc.timedeltaOneUnit(1, Rolling_WindowUnit)*Rolling_Window/dtMeasure)#24*7
	RatesUnitFactor = timedelta(days = 1)/dtMeasure 
 

	if TestCol == 0:
		df1 = df1<AlphaLim
		df2 = df2<AlphaLim
		df1TF = df1.iloc[:,0]
		df2TF = df2.iloc[:,0]
	else:
		df1Min = df1[TestCol].values == df1.iloc[:,1:].min(axis=1).values
		df2Min = df2[TestCol].values == df2.iloc[:,1:].min(axis=1).values

		df1 = df1<AlphaLim
		df2 = df2<AlphaLim
		df1TF = df1.iloc[:,0]&df1[TestCol]
		df2TF = df2.iloc[:,0]&df2[TestCol]
	
	dfFaults = pd.DataFrame( df1TF & df2TF, index = index)
	Col = dfFaults.columns[0]
	
	df = pd.DataFrame(index=index,
		data = {"value_grp" : (dfFaults[Col] != dfFaults[Col].shift(1)).cumsum()}
		)
	Starts = []
	Stops = []
	Durations = []
	for i in range(1,df['value_grp'].max()+1):
		D0 = df[df['value_grp'] == i].index[0]
		D1 = df[df['value_grp'] == i].index[-1]
		#abs((D1 - D0) / dtMeasure) > 0 and
		if abs((D1 - D0) / dtMeasure) > NDur and dfFaults[Col][D0] == True and dfFaults[Col][D1] == True:
			Starts.append( D0 - dtMeasure / 2 )
			Stops.append( D1  + dtMeasure / 2 )
			Durations.append( (D1 - D0) / dtMeasure + 1 )


	Highlighted = pd.DataFrame(
		data = { "Starts": Starts,
			"Stops" : Stops,
			"Duration": Durations,
			
		}, 
	)

	dfFaults[Col] *= 0
	for Ri in range(Highlighted.shape[0]):
		D0 = Highlighted.iloc[Ri]["Starts"]
		D1 = Highlighted.iloc[Ri]["Stops"]
		dfFaults[Col][D0:D1] = 1
	dfFaults[Col].iloc[:7] = 0
	dfRates = pd.DataFrame(
		data = { 
			"Rate" : (dfFaults[Col].rolling(RollingWinSize*2, min_periods=1).mean().values*(RatesUnitFactor)),
			},
		index = dfFaults.index,
	)

	
	return Highlighted, dfRates

def PCARegionsCollect(Ts, Qs, dtMeasure, AlphaLim, NPCA, TestCol, NDur=0):
	''' 
	Ts: The t squared hotelling statistic df. Overall and individual
	Qs: The Q resisduals statistic df. Overall and individual
	dtMeasure: A timedelta object of distance between measurments	
	AlphaLim: The P value cut off for our certainty cuts and flagging of anomalous points
	NPCA: The dimensionality of the model used, 
	TestCol: String, specific variable to look for issues.
	NDur: Minumum number of flag points.
	Return,
	Data: Scaled variables
	HighlightedAll: The regions violating the limits.
	HighlightedSpecific: The regions violating the limits with TestCol dominant
	'''
	Rows, Cols = Ts.shape[0], Ts.shape[1]-1

	AlphaLimQ = AlphaLim
	#Qs not valid if NPCA == NFeatures. 
	if NPCA == Cols:
		Qs.iloc[:,:] = 0.0

		
	#check where both Ts and Qs < AlphaLim
	HighlightedAll, dfRatesAll = GetRegions(Ts, Qs, Ts.index, dtMeasure, AlphaLim, 0, NDur)
	HighlightedSpecific, dfRatesSpecific = GetRegions(Ts, Qs, Ts.index, dtMeasure, AlphaLim, TestCol, NDur)
	return HighlightedAll, HighlightedSpecific, dfRatesAll, dfRatesSpecific 


#######################
# PCA
#######################

def PCA(df, NPCA, window):
	''' Run PCA on the given dataframe and return t squared and Q statistics over time for a rolling time inteval.
	df: The dataframe containing all our features over time.
	NPCA: The dimensionality of the model used, 
	window: The number of points to use in the rolling window
	Return,
	Data: Scaled variables
	Ts: The t squared hotelling statistic df. Overall and individual
	Qs: The Q resisduals statistic df. Overall and individual
	Variances: The fractional variance in each component over time
	'''
	df = df.diff(1).iloc[1:,:]
	Rows, Cols = df.shape[0], df.shape[1]
	
	
	## #First fit over the window
	DATA = df.iloc[:window,:]
	#Refit data
	scaler = StandardScaler()
	scaler.fit(DATA)

	#PCA
	pca = decomposition.PCA(n_components=Cols)
	pca.fit(scaler.transform(DATA))

	loadings_p = pca.components_[:,:NPCA]
	loadings_pInv = pca.components_[:NPCA,:]
	eigenvalues = pca.explained_variance_[:NPCA]
	theta = [np.sum(pca.explained_variance_[NPCA:]), np.sum(pca.explained_variance_[NPCA:]**2), np.sum(pca.explained_variance_[NPCA:]**3)]
	
	#Confidence bounds
	Data = pd.DataFrame( data = np.zeros((Rows,Cols)), columns = list(df.columns), index=df.index )
	Variances = pd.DataFrame( data = np.zeros((Rows,Cols)), columns = ["%s" % C for C in range(Cols)], index=df.index )
	Ts = pd.DataFrame( data = np.zeros((Rows,Cols+1)), columns = ["Ts"] + list(df.columns), index=df.index )
	Qs = pd.DataFrame( data = np.zeros((Rows,Cols+1)), columns = ["Qs"] + list(df.columns), index=df.index )

	#Look at components contrabution to T and Q statistics
	VectorTrans = np.zeros(NPCA)
	VectorRescale = np.zeros(Cols)	


	#TrackVariances 
	Variances.iloc[:window, :] = pca.explained_variance_ / np.sum(pca.explained_variance_)

	
	
	for H_i in range(Rows):	
		#Run over all windows...
		#New Datum
		dat_i = df.iloc[H_i,:].values.reshape(1, -1)
			
		#Check stats w.r.t. old model
		#Recalc now accepted
		Rescaledi = scaler.transform(dat_i)
		Transformedi = pca.transform(Rescaledi)[:,:NPCA]
		Rescaledi = Rescaledi[0]
		Transformedi = Transformedi[0]

		#Want PCA returned on Rescaled returned?
		Data.iloc[H_i,:] = scaler.transform(dat_i)
		Qi = abs( (Rescaledi.T).dot(Rescaledi) - 
			np.dot( 
				np.dot(Transformedi,loadings_pInv).T, 
				np.dot(Transformedi,loadings_pInv) 
				) 
			)
		Ti = Transformedi.T.dot(np.diag(eigenvalues ** -1)).dot(Transformedi)
		

		#Save data to array
		Variances.iloc[H_i,:] = pca.explained_variance_ / np.sum(pca.explained_variance_)
		#Statistics
		Ts["Ts"].iloc[H_i] = TLimInv(Ti, NPCA, window)
		Qs["Qs"].iloc[H_i] = QLimInv(Qi, theta)[1]

	
		#Look at components contrabution to T and Q statistics
		for i in range(Cols):
			VectorTrans[:] = 0
			VectorRescale[:] = 0
			
			VectorRescale[i] = scaler.transform(dat_i)[0][i]
			VectorTrans[:] = pca.transform(VectorRescale.reshape(1,-1))[:,:NPCA][0]
			
			TEi = VectorTrans.T.dot(np.diag(eigenvalues ** -1)).dot(VectorTrans)

			QEi = abs( (VectorRescale.T).dot(VectorRescale) - 
				np.dot( 
				np.dot(VectorTrans,loadings_pInv).T, 
				np.dot(VectorTrans,loadings_pInv) 
				) 
			)

			Ts[df.columns[i]].iloc[H_i] = TLimInv(TEi, NPCA, window)
			Qs[df.columns[i]].iloc[H_i] = QLimInv(QEi, theta)[1]

		if H_i < window:
			continue
		else:
			#Refit using new window
			DATA = df.iloc[H_i-window+1:H_i+1,:]

			#Refit data
			scaler = StandardScaler()
			scaler.fit(DATA)

			pca = decomposition.PCA(n_components=Cols)
			pca.fit(scaler.transform(DATA))
			loadings_p = pca.components_[:,:NPCA]
			loadings_pInv = pca.components_[:NPCA,:]
			eigenvalues = pca.explained_variance_[:NPCA]
			theta = [np.sum(pca.explained_variance_[NPCA:]), np.sum(pca.explained_variance_[NPCA:]**2), np.sum(pca.explained_variance_[NPCA:]**3)]

	return Data, Ts, Qs, Variances
			
if __name__ == "__main__":
	print("Run as module") 
