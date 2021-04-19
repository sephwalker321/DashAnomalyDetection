"""============================================================================
Module preforming Fourier and Alpha analysis functions

Contents:
- Fitting
- Fourier Transform
- Spectrum Fit
- Alpha Anaylsis

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""

import scipy
from scipy.optimize import minimize
import numpy as np
import numdifftools as nd
import pandas as pd

Alpha_MinFreq = 0

################################################################################################################
# Functions:
################################################################################################################

######################
# Fitting Functions:
######################

def ChiSqFunc(y,ymod,e):
	'''ChiSq distribution;
	y: y values,
	ymod: Model values,
	e: errors'''
	return np.sum( (y-ymod)**2 / e**2)

def modelLin(x,c,m):
	'''Linear model;
	x: x values
	c: Constant
	m: Gradient'''
	return m*x + c 

def modelSea(x, A, f, phase):
	'''Sinusoidal model;
	x: x values
	A: amplitude
	f: frequency
	phase: phase offset'''
	return A*np.cos(2.0*np.pi*x*f + phase)

def modelPink(f, A, alpha):
	'''Pink noise distribution;
	f: f values,
	A: Amplitude,
	alpha: exponent coeff'''
	return A*(f**alpha) 


######################
# Fourier Transform:
######################

def FourierTransform(Ys, units):
	'''Take the Fourier transform of data and return the Amplitude spectrum,
	Ys : Data Y values must be equally spaced unit apart
	Units : The tranformation into required units
	Returns,
	fftfreq : frequencies 
	AmpSpec : Amplitude of frequency component
	Series_phase: Phase of frequency component'''
	N = len(Ys)

	Series_fft = scipy.fft.fft(Ys)
	Series_psd = np.abs(Series_fft)
	Series_phase = np.angle(Series_fft)
	fftfreq = scipy.fft.fftfreq(len(Series_psd), 1/units)
	AmpSpec = 2*Series_psd/N

	return fftfreq, AmpSpec, Series_phase


######################
# Spectrum Fit:
######################

def FitPink(Fs, As, errs, units, guess = [1,-1]):
	'''Function to fit distribution to pink noise;
	Fs: frequencies
	As: Amplitude of frequency component
	errs: errors on As
	units: convert to appropiate units
	Returns,
	PPink: Fitted Spectrum [A, Alpha]
	PPinkErr: Fitted Spectrum Errors [A, Alpha]'''
	#Fit Pink Noise
	R = minimize(lambda Para,x=Fs,y=As,e=errs: ChiSqFunc(y,modelPink(x,Para[0],Para[1]),e), guess, bounds=[(0,None),(-2,2)], options={'gtol': 1e-6, 'disp': False})
	PPink = R.x 
	chisqvalue = R.fun #chisqmin
	chisqreduced = chisqvalue/(len(Fs)-len(PPink))

	H = nd.Hessian(lambda Para,x=Fs,y=As,e=errs: ChiSqFunc(y,modelPink(x,Para[0],Para[1]),e))([PPink[0],PPink[1]])
	if np.isnan(np.sum(H)) == False and np.linalg.det(H) != 0:
		ErrorM = scipy.linalg.inv(H/2)
		PPinkErrs = np.array( [abs(ErrorM[0,0])**0.5,abs(ErrorM[1,1])**0.5] )
	else: 
		PPinkErrs = np.array( [np.inf, np.inf] )
		PPink = [0,0]
		
	return PPink, PPinkErrs

######################
# Alpha Anaylsis:
######################

def AlphasProgress(data, WinSize, errs, units, Name):
	'''Sliding window anaysis of data, spectrum is fit to A*f^alpha model, then run through bayesian online change point detection;
	data: Raw data of variable,
	WinSize: Int number of data points corresponding to the desired window size,
	units: convert to appropiate units,
	Name: The varible name
	Return,
	df: Dataframe of rolling window Alphas and fitting errors '''
	#Do with control regions
	NPoints = len(data)
	PinkWindows = np.zeros((NPoints,2, 2)) - np.inf
	guess = [1,-1] #Inital guess
	for i in range(NPoints-WinSize):
		fftfreq, AmpSpec, Series_phase = FourierTransform(data[i:i+WinSize], units) 
		Fs = fftfreq[fftfreq>Alpha_MinFreq]
		As = AmpSpec[fftfreq>Alpha_MinFreq]
		#Fit Seasonality
		PPink, PPinkErrs = FitPink(Fs, As, errs, units, guess)
		PinkWindows[i+WinSize,0] = PPink
		PinkWindows[i+WinSize,1] = PPinkErrs
		#Use previous solution to help
		guess = PPink
		
		
	df = pd.DataFrame(
		data = { Name: PinkWindows[:,0,1],
			"Error" : PinkWindows[:,1,1],
		}, 
	)
	return df

if __name__ == "__main__":
	print("Run as module") 
