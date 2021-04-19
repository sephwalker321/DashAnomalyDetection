"""============================================================================
Module of ploting functions for cacheing in graphs/

Contents:
- Many Lines
- Alpha Anaylsis
- BOCPD
- PCA

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
import numpy as np

import matplotlib.pyplot as pyplot
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm as LogNorm
from matplotlib.colors import Normalize as Norm

#For manipulating datetime format
from datetime import timedelta

import os

################################################################################################################
# Functions:
################################################################################################################

######################
# Many Lines:
######################

def plotMATPLOTLIB(Xs=[],Ys=[], Errs=[], XLim=[None,None], YLim=[None,None], XScale="linear", YScale="linear", LinesVert=[], LinesHorz=[], XLabel="t", YLabel="y", Labels=[""], Colors=["black"],Linestyles=["-"], directory="", Name="", Dates=True):
	''' Plot overlaying lines and save .png.
	Xs: List of numpy arrays for x-axis
	Ys: List of numpy arrays for y-axis
	Errs: List of numpy arrays for y-axis errors
	XLim: [x0,x1] XLimit of axis
	YLim: [y0,y1] YLimit of axis
	XScale: "linear" or "log" scale for x-axis
	YScale: "linear" or "log" scale for y-axis
	LinesVert: List of x positions for vertical lines
	LinesHorz: List of y positions for horizontal lines
	XLabel: Label for x axis
	YLabel: Label for y axis
	Labels: List of labels for legend
	Colors: List of colours for lines
	Linestyles: List of linestyles for lines
	directory: Directory to save plot in
	Name: Name of file
	Dates: T/F Is the X-axis datetime values
	Return,
	1: If exit correctly.
	'''
	NDats = len(Xs)
	NVerts = len(LinesVert)
	NHorzs = len(LinesHorz)

	if NDats == 0:
		return 0

	
	days = mdates.DayLocator() # every Day
	weeks = mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)  # every Monday
	months = mdates.MonthLocator() # every month
	years = mdates.YearLocator() # every year


	fig = pyplot.figure(constrained_layout=False, figsize=(15,5))
	gs = fig.add_gridspec(1)
	ax = fig.add_subplot(gs[0])
	
	sig = BOCPD_errsScale
	for dat_i in range(NDats):
		ax.plot(Xs[dat_i],Ys[dat_i],color=Colors[dat_i],linestyle=Linestyles[dat_i], label=Labels[dat_i])
		if isinstance(Errs[dat_i], (list, tuple, np.ndarray)):
			ax.fill_between(Xs[dat_i], Ys[dat_i]-sig*Errs[dat_i], Ys[dat_i]+sig*Errs[dat_i], color='red', alpha=0.4)
	for vert_i in range(NVerts):
		ax.axvline(LinesVert[vert_i],color="gray",linestyle="--")
	for horz_i in range(NHorzs):
		ax.axhline(LinesHorz[horz_i],color="gray",linestyle="--")

	
	ax.set_xlim(XLim)
	ax.set_ylim(YLim)
	ax.set_xlabel(XLabel)
	ax.set_ylabel(YLabel)
	ax.set_yscale(YScale)
	ax.set_xscale(XScale)
	if Dates == True:
		if (Xs[0][-1] - Xs[0][0])/ timedelta(weeks=52*2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax.xaxis.set_major_formatter(xfmt)
			ax.xaxis.set_minor_locator(months)
			ax.xaxis.set_major_locator(years)
		if (Xs[0][-1] - Xs[0][0])/ timedelta(weeks=4*6) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax.xaxis.set_major_formatter(xfmt)
			ax.xaxis.set_minor_locator(weeks)
			ax.xaxis.set_major_locator(months)
		if (Xs[0][-1] - Xs[0][0])/ timedelta(weeks = 2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax.xaxis.set_major_formatter(xfmt)
			ax.xaxis.set_minor_locator(days)
			ax.xaxis.set_major_locator(weeks)
	if len(Labels) > 1:
		ax.legend()
	
	if directory != "":
		pyplot.savefig(directory+os.sep+Name+".png")
	pyplot.close()
	return 1

######################
# Alpha Anaylsis:
######################

def plotMATPLOTLIBAlpha(Data, Alpha, XLim=[None,None], YLim=[None,None] , directory="", Name="", Dates=True):
	''' Plot Alpha data and data for series.
	Data: dataframe of raw data
	Alpha: dataframe of Alpha data
	XLim: [x0,x1] XLimit of axis
	YLim: [y0,y1] YLimit of axis
	directory: Directory to save plot in
	Name: Name of file
	Dates: T/F Is the X-axis datetime values
	Return,
	1: If exit correctly.
	'''
	days = mdates.DayLocator() # every Day
	weeks = mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)  # every Monday
	months = mdates.MonthLocator() # every month
	years = mdates.YearLocator() # every year

	

	fig = pyplot.figure(constrained_layout=False, figsize=(15,5))
	gs = fig.add_gridspec(3,1)
	gs.update(hspace=0)
	ax1 = fig.add_subplot(gs[:-1,0]) #Alpha
	ax2 = fig.add_subplot(gs[-1,0], sharex=ax1) #Raw
	
	sig = BOCPD_errsScale
	Cols = Data.columns
	ax1.plot(Alpha.index, Alpha.iloc[:,0], color="black")
	ax1.fill_between(Alpha.index, Alpha.iloc[:,0]-sig*Alpha["Error"], Alpha.iloc[:,0]+sig*Alpha["Error"], color='red', alpha=0.4)

	ax2.plot(Data.index, Data[Cols[0]],label=Cols[0], color="black")
	ax2.fill_between(Data.index, Data[Cols[0]]-sig*Data["Error"], Data[Cols[0]]+sig*Data["Error"], color='red', alpha=0.4)

	ax1.axhline(-2,color="gray",linestyle="--")
	ax1.axhline(-1,color="gray",linestyle="--")
	ax1.axhline(0,color="gray",linestyle="--")
	
	ax1.set_xlim(XLim)
	ax1.set_ylim([None,None])
	ax1.set_ylim([-2,0])
	ax2.set_xlabel("Time, t")
	ax1.set_ylabel(r"Alpha, $\alpha$")
	ax2.set_ylabel(Cols[0])

	if Dates == True:
		if (Data.index[-1] - Data.index[0])/ timedelta(weeks=52*2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax1.xaxis.set_major_formatter(xfmt)
			ax1.xaxis.set_minor_locator(months)
			ax1.xaxis.set_major_locator(years)
		if (Data.index[-1] - Data.index[0])/ timedelta(weeks=4*6) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax1.xaxis.set_major_formatter(xfmt)
			ax1.xaxis.set_minor_locator(weeks)
			ax1.xaxis.set_major_locator(months)
		if (Data.index[-1] - Data.index[0])/ timedelta(weeks = 2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax1.xaxis.set_major_formatter(xfmt)
			ax1.xaxis.set_minor_locator(days)
			ax1.xaxis.set_major_locator(weeks)
	#ax1.legend()
	pyplot.setp(ax1.get_xticklabels(),visible=False)
	if directory != "":
		pyplot.savefig(directory+os.sep+Name+".png")
	pyplot.close()
	return 1

######################
# BOCPD:
######################

def plotMATPLOTLIBBOCPDHeat(Xs,Ys, Errs, RMaxes, R, tol, dT, XLim=[None,None], YLim=[None,None], LinesVert=[], XLabel="t", YLabel="y", directory="", Name="", Dates=True):
	''' Plot BOCPD heatmap and series below and save .png.
	Xs: List of numpy arrays for x-axis
	Ys: List of numpy arrays for y-axis
	Errs: List of numpy arrays for y-axis errors
	RMaxes: Most likely sequence length
 	R: BOCPD matrix
	tol: BOCPD tolerance limit
	dT: datetime interval of sample rate
	XLim: [x0,x1] XLimit of axis
	YLim: [y0,y1] YLimit of axis
	XScale: "linear" or "log" scale for x-axis
	YScale: "linear" or "log" scale for y-axis
	LinesVert: List of x positions for vertical lines
	XLabel: Label for x axis
	YLabel: Label for y axis
	directory: Directory to save plot in
	Name: Name of file
	Dates: T/F Is the X-axis datetime values
	Return,
	1: If exit correctly.
	'''
	days = mdates.DayLocator() # every Day
	weeks = mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)  # every Monday
	months = mdates.MonthLocator() # every month
	years = mdates.YearLocator() # every year

	norm = LogNorm(vmin=tol, vmax=1.0)
	MatXs =  Xs[0]-0.5*dT + np.arange(R.shape[0]+1)*dT
	MatYs = np.arange(-0.5,R.shape[1],1)
	

	fig = pyplot.figure(constrained_layout=True, figsize=(15,5))
	gs = fig.add_gridspec(3,1)
	gs.update(hspace=0)
	ax1 = fig.add_subplot(gs[:-1,0])
	ax2 = fig.add_subplot(gs[-1,0], sharex=ax1)
	
	
	c = ax1.pcolor(MatXs,MatYs, np.transpose(R), cmap='gray_r', norm=norm)
	fig.colorbar(c, ax=[ax1,ax2,], fraction=0.03)
	ax1.plot(Xs,RMaxes,color="red")
	ax2.plot(Xs,Ys,color="black")
	sig = BOCPD_errsScale
	if isinstance(Errs, (list, tuple, np.ndarray)):
		ax2.fill_between(Xs, Ys-sig*Errs, Ys+sig*Errs, color='red', alpha=0.4)
	for Vert_i in range(len(LinesVert)):
		ax1.axvline(LinesVert[Vert_i],color='orange',linestyle='--')
		ax2.axvline(LinesVert[Vert_i],color='orange',linestyle='--')


	ax1.set_xlim(XLim)
	ax1.set_ylim(YLim)
	ax2.set_xlabel(XLabel)
	ax1.set_ylabel("seq length, l")
	ax2.set_ylabel(YLabel)
	if Dates == True:
		if (Xs[-1] - Xs[0])/ timedelta(weeks=52*2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax2.xaxis.set_major_formatter(xfmt)
			ax2.xaxis.set_minor_locator(months)
			ax2.xaxis.set_major_locator(years)
		if (Xs[-1] - Xs[0])/ timedelta(weeks=4*6) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax2.xaxis.set_major_formatter(xfmt)
			ax2.xaxis.set_minor_locator(weeks)
			ax2.xaxis.set_major_locator(months)
		if (Xs[-1] - Xs[0])/ timedelta(weeks=2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax2.xaxis.set_major_formatter(xfmt)
			ax2.xaxis.set_minor_locator(days)
			ax2.xaxis.set_major_locator(weeks)
	pyplot.setp(ax1.get_xticklabels(),visible=False)
	#pyplot.setp(axNull.get_xticklabels(),visible=False)
	#pyplot.setp(axNull.get_yticklabels(),visible=False)
	if directory != "":
		pyplot.savefig(directory+os.sep+Name+".png")
	pyplot.close()
	return 1

######################
# PCA:
######################

def plotMATPLOTLIBPCA(DataPCA, Ts, Qs, XLim=[None,None], YLim=[None,None], LinesHorz=[], RegionsA=0, RegionsS=0 , directory="", Name="", Dates=True):
	''' Plot overlaying lines and save .png.
	DataPCA: Dataframe of rescaled features
	Ts: Dataframe of T-Hoteling Statistics "Ts", Var_1, Var_2,
	Qs: Dataframe of Qs Statistics "Qs", Var_1, Var_2,
	XLim: [x0,x1] XLimit of axis
	YLim: [y0,y1] YLimit of axis
	LinesHorz: List of y positions for horizontal lines
	RegionsA: Dataframe of regions which violate Ts Qs Limits
	RegionsS: Dataframe in which Var_1 is dominatant Limit violator
	directory: Directory to save plot in
	Name: Name of file
	Dates: T/F Is the X-axis datetime values
	Return,
	1: If exit correctly.
	'''
	import matplotlib.pyplot as pyplot
	import matplotlib.dates as mdates
	days = mdates.DayLocator() # every Day
	weeks = mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)  # every Monday
	months = mdates.MonthLocator() # every month
	years = mdates.YearLocator() # every year

	

	fig = pyplot.figure(constrained_layout=False, figsize=(15,5))
	gs = fig.add_gridspec(3,1)
	gs.update(hspace=0)
	ax1 = fig.add_subplot(gs[0,0]) # Features
	ax2 = fig.add_subplot(gs[1,0], sharex=ax1) # Ts
	ax3 = fig.add_subplot(gs[2,0], sharex=ax2) # Qs

	Cols = DataPCA.columns
	cmap = pyplot.get_cmap("nipy_spectral")
	c = cmap(np.linspace(.2,1,len(Cols)))
	for i in range(len(Cols)):
		ax1.plot(DataPCA.index, DataPCA[Cols[i]],label=Cols[i], c=c[i])
		ax2.plot(Ts.index, Ts[Cols[i]], c=c[i])
		ax3.plot(Qs.index, Qs[Cols[i]], c=c[i])

	ax2.plot(Ts.index, Ts["Ts"], c="black")
	ax3.plot(Qs.index, Qs["Qs"], c="black")
	

	for horz_i in range(len(LinesHorz)):
		ax2.axhline(LinesHorz[horz_i],color="red",linestyle="--")
		ax3.axhline(LinesHorz[horz_i],color="red",linestyle="--")
	for Ri in range(RegionsA.shape[0]):
		ax1.axvspan(RegionsA.iloc[Ri]["Starts"], RegionsA.iloc[Ri]["Stops"], color='orange', alpha=0.2)
		ax2.axvspan(RegionsA.iloc[Ri]["Starts"], RegionsA.iloc[Ri]["Stops"], color='orange', alpha=0.2)
		ax3.axvspan(RegionsA.iloc[Ri]["Starts"], RegionsA.iloc[Ri]["Stops"], color='orange', alpha=0.2)
	for Ri in range(RegionsS.shape[0]):
		ax1.axvspan(RegionsS.iloc[Ri]["Starts"], RegionsS.iloc[Ri]["Stops"], color='red', alpha=0.2)
		ax2.axvspan(RegionsS.iloc[Ri]["Starts"], RegionsS.iloc[Ri]["Stops"], color='red', alpha=0.2)
		ax3.axvspan(RegionsS.iloc[Ri]["Starts"], RegionsS.iloc[Ri]["Stops"], color='red', alpha=0.2)

	
	ax1.set_xlim(XLim)
	ax1.set_ylim([None,None])
	ax2.set_ylim(YLim)
	ax3.set_ylim(YLim)
	ax3.set_xlabel("Time, t")
	ax1.set_ylabel("Feature")
	ax2.set_ylabel(r"$T^{2}$")
	ax3.set_ylabel(r"$Q$")
	ax1.set_yscale('linear')
	ax2.set_yscale('log')
	ax3.set_yscale('log')
	if Dates == True:
		if (DataPCA.index[-1] - DataPCA.index[0])/ timedelta(weeks=52*2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax1.xaxis.set_major_formatter(xfmt)
			ax1.xaxis.set_minor_locator(months)
			ax1.xaxis.set_major_locator(years)
		if (DataPCA.index[-1] - DataPCA.index[0])/ timedelta(weeks=4*6) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax1.xaxis.set_major_formatter(xfmt)
			ax1.xaxis.set_minor_locator(weeks)
			ax1.xaxis.set_major_locator(months)
		if (DataPCA.index[-1] - DataPCA.index[0])/ timedelta(weeks = 2) < 1:
			xfmt = mdates.DateFormatter('%Y-%m-%d')
			ax1.xaxis.set_major_formatter(xfmt)
			ax1.xaxis.set_minor_locator(days)
			ax1.xaxis.set_major_locator(weeks)
	ax1.legend()
	pyplot.setp(ax1.get_xticklabels(),visible=False)
	pyplot.setp(ax2.get_xticklabels(),visible=False)
	
	if directory != "":
		pyplot.savefig(directory+os.sep+Name+".png")
	pyplot.close()
	return 1

		
if __name__ == "__main__":
	print("Run as module") 
