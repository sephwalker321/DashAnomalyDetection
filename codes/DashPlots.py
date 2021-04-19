"""============================================================================
Module of Dashboard plotting functions

Contents:
- Raw Features
- Fourier
- Alpha
- BOCPD
- PCA
- Empty

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
import numpy as np
#For manipulating datetime format
from datetime import datetime
# Plotly code for graphing
import plotly.graph_objects as go
import sys
import os
if sys.argv[0] == "JustRun.py":
	from EDFApp.codes import Misc
	from EDFApp.codes import Fourier
if sys.argv[0].split(os.sep)[-1] == "app.py":
	from codes import Misc
	from codes import Fourier

################################################################################################################
# Dashboard Figures Code
################################################################################################################

######################
# Figures Code: Raw Fig
######################

def CreateRawFig(data, sig, Data_i_Name, WindowParameters, Height):
	''' Raw figure plots for tabs 1 and 2.
	data: A dataframe of data with columns [feature, error],
	sig: Error scaling factor,
	Data_i_Name: The Column feature name
	WindowParameters: A dictionary of key statistics {"Mean", "STD", "Start", "End", "Rate", "RateUnit", "Duration", "Min", "Max"}
	Height: Height in pixels required. (Width autoscales)
	Return,
	Fig: A figure html element.'''
	YRange = [np.min(data[Data_i_Name]-data["Error"].mean()*3),np.max(data[Data_i_Name]+data["Error"].mean()*3)]
	XRange = [data.index[0], data.index[-1]]
	if sig == None:
		sig = 0

	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":"Amplitude, A",
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			"yaxis_range":YRange,
			}
	)
	
	# Add traces
	Fig.add_trace(
		go.Scatter(
			x=data.index, y=data[Data_i_Name], name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 1, "color":"black"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)

	#Error highlights
	Fig.add_trace(
		go.Scatter(
			x=data.index, y=data[Data_i_Name]+data["Error"]*sig, name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 0, "color":"red"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)
	Fig.add_trace(
		go.Scatter(
			x=data.index, y=data[Data_i_Name]-data["Error"]*sig, name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 0, "color":"red"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
			fill='tonexty',
		)
	)

	Fig.add_shape( 
		fillcolor="#68246D",
		opacity=0.2,
		line={"width": 0},
		type="rect",
		x0=Misc.unixToDatetime(WindowParameters["Start"]),
		x1=Misc.unixToDatetime(WindowParameters["End"]),
		xref="x",
		#y0=WindowParameters["Min"],
		#y1=WindowParameters["Max"],
		y0=YRange[0],
		y1=YRange[1],
		yref="y",
		layer='below',	
	),
	return Fig

def CreateRawFigStacked(data, error, sig, Features, WindowParameters, Height):
	''' Raw figure plots for tabs 1 and 2.
	data: A dataframe of data with columns [features],
	error: A dataframe of error with columns [errors],
	sig: Error scaling factor,
	Features: The Column feature names,
	WindowParameters: A dictionary of key statistics {"Mean", "STD", "Start", "End", "Rate", "RateUnit", "Duration", "Min", "Max"}
	Height: Height in pixels required. (Width autoscales)
	Return,
	Fig: A figure html element.'''
	YRange = [np.min(data.min()-error.mean()*3),np.max(data.max()+error.mean()*3)]
	XRange = [data.index[0], data.index[-1]]
	if sig == None:
		sig = 0

	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":"Amplitude, A",
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			"yaxis_range":YRange,
			}
	)
	
	for Data_i_Name in Features:
		# Add traces
		Fig.add_trace(
			go.Scatter(
				x=data.index, y=data[Data_i_Name], name="",
				hoverinfo="name+x+y",
				hovertemplate= "<br>N: %s" % (Data_i_Name)+"<br>t: %{x}<br>"+"y: %{y:.2f}",
				line={"width": 1, "color":"black"},
				marker={"size": 5},
				mode="lines",
				showlegend=False,
			)
		)

		#Error highlights
		Fig.add_trace(
			go.Scatter(
				x=data.index, y=data[Data_i_Name]+error[Data_i_Name]*sig, name="",
				hoverinfo="name+x+y",
				hovertemplate= "<br>N: %s" % (Data_i_Name)+"<br>t: %{x}<br>"+"y: %{y:.2f}",
				line={"width": 0, "color":"red"},
				marker={"size": 5},
				mode="lines",
				showlegend=False,
			)
		)
		Fig.add_trace(
			go.Scatter(
				x=data.index, y=data[Data_i_Name]-error[Data_i_Name]*sig, name="",
				hoverinfo="name+x+y",
				hovertemplate= "<br>N: %s" % (Data_i_Name)+"<br>t: %{x}<br>"+"y: %{y:.2f}",
				line={"width": 0, "color":"red"},
				marker={"size": 5},
				mode="lines",
				showlegend=False,
				fill='tonexty',
			)
		)

	Fig.add_shape( 
		fillcolor="#68246D",
		opacity=0.2,
		line={"width": 0},
		type="rect",
		x0=Misc.unixToDatetime(WindowParameters["Start"]),
		x1=Misc.unixToDatetime(WindowParameters["End"]),
		xref="x",
		#y0=WindowParameters["Min"],
		#y1=WindowParameters["Max"],
		y0=YRange[0],
		y1=YRange[1],
		yref="y",
		layer='below',	
	),
	return Fig

######################
# Figures Code: Fourier Fig
######################

def CreateFFTFig(Xs,Ys, PPink, Height, YRange, MinFreq, LinLog, Data_i_Name):
	''' Raw figure plots for tabs 1 and 2.
	Xs: The frequencies
	Ys: The Amplitudes
	PPink: Fitted Pink Noise, [A,alpha]
	Height: Height in pixels required. (Width autoscales)
	YRange: [Min,Max] An expected Min and Max for the plot over all windowed regions
	MinFreq: The Minimum Frequence used for fitting
	LinLog: "Linear" or "Log" determines lin or log nature of y axis
	Data_i_Name: The Column varaible name
	Return,
	Fig: A figure html element.'''
	XRange = [1,24*365*2]
	Fig = go.Figure(
		layout= {
			"xaxis_title":"frequency, f [1/year]",
  			"yaxis_title":"Amplitude, A",
			"autosize":True,
			"margin":{"l":10,"r":10,"t":10,"b":10},
			"height":Height,
		}
	)
	if LinLog == "Log":
		Fig.update_layout(
			{"xaxis_range":np.log10(XRange),
			"yaxis_range":np.log10(YRange),
			"xaxis_type":'log',
			"yaxis_type":'log'},
		)
	if LinLog == "Linear":
		Fig.update_layout(
			{"xaxis_range":np.log10(XRange),
			"yaxis_range":YRange,
			"xaxis_type":'log',
			"yaxis_type":'linear'},
		)

	# Add traces
	Fig.add_trace(
		go.Scatter(
			x=Xs,y=Ys,
			hoverinfo="x+y",
			hovertemplate= "<br>f: %{x:.2f}<br>"+"A: %{y:.2f}<extra></extra>",
			line={"width": 1, "color":"black"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		),
	)

	XModel = np.logspace(np.log10(XRange[0]), np.log10(XRange[1]), 1000)
	YModel = Fourier.modelPink(XModel, PPink[0], PPink[1])
	Fig.add_trace(
		go.Scatter(
			x=XModel,y=YModel,
			hoverinfo="x+y",
			hovertemplate= "<br>f: %{x:.2f}<br>"+"A: %{y:.2f}<extra></extra>",
			line={"width": 1, "color":"red"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		),
	)
	
	#Daily Harmonics
	KeyFreqs = [365,365*2,365*3,365*4,365*5,365*6,365*7,365*8,365*9,365*10,365*11,365*12]
	for Fi in range(len(KeyFreqs)):
		FreqLine = KeyFreqs[Fi]
		if FreqLine < XRange[0]:
			continue 
		if FreqLine > XRange[1]:
			break 
		Fig.add_shape(
			type="line",
			x0=FreqLine, y0=YRange[0], x1=FreqLine, y1=YRange[1],
			line={
	    		"color":"gray",
	    		"width":1,
	    		"dash":"dash",
			}
		)

	Fig.add_shape(
		type="line",
		x0=MinFreq, y0=YRange[0], x1=MinFreq, y1=YRange[1],
		line={
	    	"color":"red",
	    	"width":1,
	    	"dash":"dot",
		}
	)

	#Weekly harmonics
	KeyFreqs = [52]
	for Fi in range(len(KeyFreqs)):
		FreqLine = KeyFreqs[Fi]
		if FreqLine < XRange[0]:
			continue 
		if FreqLine > XRange[1]:
			break 
		Fig.add_shape(
			type="line",
			x0=FreqLine, y0=YRange[0], x1=FreqLine, y1=YRange[1],
			line={
	    		"color":"gray",
	    		"width":1,
	    		"dash":"dot",
			}
		)
	#For range fixing only. (Invisable line)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[0], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[1], y1=YRange[0],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[1], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)

	return Fig

######################
# Figures Code: Alphas Fig
######################

def CreateAlphasFig(Alphasdf, WindowParameters, sig, Height, Name):
	''' Example Alpha plots.
	Alphasdf:df "Alpha" and "Errs" values at each timestep
	WindowParameters: A dictionary of key statistics {"Mean", "STD", "Start", "End", "Rate", "RateUnit", "Duration", "Min", "Max"}
	Sig: Error multiplier,
	Height: Height in pixels required. (Width autoscales)
	Name: name for saving figure
	Return,
	Fig: A figure html element.'''
	YRange = [-2.5,0.5]
	XRange = [Alphasdf.index[0],Alphasdf.index[-1]]
	if sig == None:
		sig = 0
	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":"Alpha, \u03B1",
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			"xaxis_range":XRange,
			"yaxis_range":YRange,
			}
	)

	#Error highlights
	Fig.add_trace(
		go.Scatter(
			x=Alphasdf.index, y=Alphasdf[Name]+Alphasdf["Error"]*sig, name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 0, "color":"red"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)
	Fig.add_trace(
		go.Scatter(
			x=Alphasdf.index, y=Alphasdf[Name]-Alphasdf["Error"]*sig, name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 0, "color":"red"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
			fill='tonexty',
		)
	)

	# Add traces
	Fig.add_trace(
		go.Scatter(
			x=Alphasdf.index, y=Alphasdf[Name], name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 1, "color":"black"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)
	#For eye guide
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=0, x1=XRange[1], y1=0,
			line={
	    		"width":1,
			"color":"white",
			"dash":"dash",
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=-1, x1=XRange[1], y1=-1,
			line={
	    		"width":1,
			"color":"purple",
			"dash":"dash",
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)

	#For range fixing only. (Invisable line)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[0], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	return Fig

######################
# Figures Code: BOCPD Fig
######################

def CreateBOCPDFig(BOCPDdf, R_Max, Lines, WindowParameters, tol, Height):
	''' Example Alpha plots.
	BOCPDdf:df "Alpha" and "Errs" values at each timestep
	R_Max: The Most likely sequence length at time t
	Lines: timestamps where R_Max is a 0 length sequence
	WindowParameters: A dictionary of key statistics {"Mean", "STD", "Start", "End", "Rate", "RateUnit", "Duration", "Min", "Max"}
	Sig: Error multiplier,
	tol: The P value truncation size
	Height: Height in pixels required. (Width autoscales)
	Return,
	Fig: A figure html element.'''
	Zmin = np.log10(tol)
	Zs = np.nan_to_num(np.log10(BOCPDdf.values.T), nan=-np.inf,posinf=np.inf, neginf=-np.inf)

	YRange = [0,np.max(R_Max)+20]
	XRange = [Misc.unixToDatetime(WindowParameters["Start"]),Misc.unixToDatetime(WindowParameters["End"])]
	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":"Seq length, l",
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			"xaxis_range":XRange,
			"yaxis_range":YRange,
			"plot_bgcolor":'white',
			}
	)

	Fig.add_trace(
		go.Heatmap(
			x=BOCPDdf.index,
			y=BOCPDdf.columns, 			
			z=Zs, 
			customdata=10**Zs,
			name = "",
			hoverinfo="x+y+z+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}<br>"+"z: %{customdata:.5f}",
			zmax = 0,
			zmin = Zmin,
			showscale = False,
			colorscale='purples'		
		)
	)
	
	#Error highlights
	Fig.add_trace(
		go.Scatter(
			x=BOCPDdf.index, y=R_Max, name="",
			hoverinfo="x+y+text",
			hovertemplate= "<br>t: %{x}<br>"+"y: %{y:.2f}",
			line={"width": 2, "color":"black"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)

	for X_i in Lines:
		Fig.add_shape(
			type="line",
			x0=X_i, y0=YRange[0], x1=X_i, y1=YRange[1],
			line={
	    		"width":1,
				"color":"black",
				"dash":"dash",
			}
		)

	#Bounding box for double-click reset
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[1], y1=YRange[0],
			line={
	    		"width":1,
			"color":"purple",
			"dash":"dash",
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)

	#For range fixing only. (Invisable line)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[0], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	return Fig

######################
# Figures Code: PCA
######################

def CreatePCADataFig(Data, RegionsA, RegionsS, TestCol, NDur, Height):
	''' Example Alpha plots.
	Data: Dataframe of T or Q statistics overall for all features then marginalised for each.
	RegionsA : Dataframe of Regions where alpha_crit violated overall
	RegionsS :  Dataframe of Regions where requested feature is violated
	Height: Height in pixels required. (Width autoscales),
	Return,
	Fig: A figure html element.'''
	YRange = [-7.5, 7.5]
	XRange = [Data.index[0], Data.index[-1]]
	Cols = Data.columns


	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":"Feature",
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			#"xaxis_type":'log',
			"xaxis_range":XRange,
			#"yaxis_type":'log',
			"yaxis_range":YRange,
			"plot_bgcolor":'white',
			}
	)

	#Highlight flagged regions
	for PCAi in range(len(Cols)):
		Data.iloc[:,PCAi][Data.iloc[:,PCAi] > 7.5] = 7.5
		Data.iloc[:,PCAi][Data.iloc[:,PCAi] < -7.5] = -7.5

	if TestCol == None:
		for PCAi in range(len(Cols)):		
			Fig.add_trace(
				go.Scatter(
					x=Data.index, y=Data.iloc[:,PCAi], name="",
					hoverinfo="name+x+y",
					hovertemplate= "<br>N: %s" % (Cols[PCAi])+"<br>t: %{x}<br> y: %{y:.2f}",
					line={"width": 1, "color": "black"},
					marker={"size": 5},
					mode="lines",
					showlegend=False,
				)
			)
	else:
		Fig.add_trace(
			go.Scatter(
				x=Data.index, y=Data[TestCol], name="",
				hoverinfo="name+x+y",
				hovertemplate= "<br>N: %s" % (TestCol)+"<br>t: %{x}<br> y: %{y:.2f}",
				line={"width": 1, "color": "purple"},
				marker={"size": 5},
				mode="lines",
				showlegend=False,
			)
		)

	for Ri in range(RegionsA.shape[0]):
		if RegionsA.iloc[Ri]["Duration"] <= NDur:
				continue
		Fig.add_shape( 
			fillcolor="orange",
			opacity=0.4,
			line={"width": 0},
			type="rect",
			x0=Misc.unixToDatetime(RegionsA.iloc[Ri]["Starts"]),
			x1=Misc.unixToDatetime(RegionsA.iloc[Ri]["Stops"]),
			xref="x",
			y0=YRange[0],
			y1=YRange[1],
			yref="y",
			layer='above',	
		),
	if isinstance(RegionsS, (int)):
		pass
	else:
		for Ri in range(RegionsS.shape[0]):
			if RegionsS.iloc[Ri]["Duration"] <= NDur:
				continue
			Fig.add_shape( 
				fillcolor="red",
				opacity=0.4,
				line={"width": 0},
				type="rect",
				x0=Misc.unixToDatetime(RegionsS.iloc[Ri]["Starts"]),
				x1=Misc.unixToDatetime(RegionsS.iloc[Ri]["Stops"]),
				xref="x",
				y0=YRange[0],
				y1=YRange[1],
				yref="y",
				layer='above',	
			),

	#Bounding box for double-click reset
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[1], y1=YRange[0],
			line={
	    		"width":0,
			"color":"purple",
			"dash":"dash",
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)

	#For range fixing only. (Invisable line)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[0], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	return Fig


#DISUSED ########################################################
def CreatePCAFig(Label, AlphaLim, Stats, RegionsA, RegionsS, Height):
	''' Example Alpha plots.
	Label: The y axis label, T or Q.
	AlphaLim: The Criteria Limit
	Stats: The Pvalues of the T or Q stat
	RegionsA : Dataframe of Regions where alpha_crit violated overall
	RegionsS :  Dataframe of Regions where requested feature is violated
	Height: Height in pixels required. (Width autoscales),
	Return,
	Fig: A figure html element.'''
	YRange = [max(1e-16,Stats[Label].min()), 2]
	XRange = [Stats[Label].index[0], Stats.index[-1]]

	Stats[Stats < YRange[0]] = YRange[0] 
	Cols = Stats.columns

	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":Label,
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			#"xaxis_type":'log',
			"xaxis_range":XRange,
			"yaxis_type":'log',
			"yaxis_range":np.log10(YRange),
			"plot_bgcolor":'white',
			}
	)

	#Error highlights
	Fig.add_trace(
		go.Scatter(
			x=Stats.index, y=Stats[Label], name="",
			hoverinfo="name+x+y",
			customdata=np.log10(Stats[Label]),
			hovertemplate= "<br>N: %s" % (Cols[0])+"<br>t: %{x}<br> y: %{customdata:.2f}",
			line={"width": 1, "color":"purple"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)

	#Highlight flagged regions
	for PCAi in range(1, len(Cols)):
		Fig.add_trace(
			go.Scatter(
				x=Stats.index, y=Stats.iloc[:,PCAi], name="",
				hoverinfo="name+x+y",
				customdata=np.log10(Stats.iloc[:,PCAi]),
				hovertemplate= "<br>N: %s" % (Cols[PCAi])+"<br>t: %{x}<br> y: %{customdata:.2f}",
				line={"width": 1, "color":"black"},
				marker={"size": 5},
				mode="lines",
				showlegend=False,
			)
		)

	#Highlight flagged regions
	for Ri in range(RegionsA.shape[0]):
		Fig.add_shape( 
			fillcolor="orange",
			opacity=0.4,
			line={"width": 0},
			type="rect",
			x0=Misc.unixToDatetime(RegionsA.iloc[Ri]["Starts"]),
			x1=Misc.unixToDatetime(RegionsA.iloc[Ri]["Stops"]),
			xref="x",
			y0=YRange[0],
			y1=YRange[1],
			yref="y",
			layer='above',	
		),
	for Ri in range(RegionsS.shape[0]):
		Fig.add_shape( 
			fillcolor="red",
			opacity=0.4,
			line={"width": 0},
			type="rect",
			x0=Misc.unixToDatetime(RegionsS.iloc[Ri]["Starts"]),
			x1=Misc.unixToDatetime(RegionsS.iloc[Ri]["Stops"]),
			xref="x",
			y0=YRange[0],
			y1=YRange[1],
			yref="y",
			layer='above',	
		),

	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=AlphaLim, x1=XRange[1], y1=AlphaLim,
			line={
	    		"width":1,
				"color":"red",
				"dash":"dash",
			}
	)
		


	#Bounding box for double-click reset
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[1], y1=YRange[0],
			line={
	    		"width":0,
			"color":"purple",
			"dash":"dash",
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)

	#For range fixing only. (Invisable line)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[0], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	return Fig

def CreateRatesFig(Label, Lim, RatesA, RatesS, RegionsA, RegionsS, TestCol, NDur, Height):
	''' Example Alpha plots.
	Label: The y axis label, T or Q.
	Lim: The Criteria Limit,
	RatesA: Averaged Rolling rates,
	RatesS: Specific Rolling rates,
	RegionsA : Dataframe of Regions where alpha_crit violated overall
	RegionsS :  Dataframe of Regions where requested feature is violated
	TestCol : The marginalised feature to examine name. String
	Height: Height in pixels required. (Width autoscales),
	Return,
	Fig: A figure html element.'''
	YRange = [0, np.max(RatesA.values)*1.2]
	XRange = [RatesA.index[0], RatesA.index[-1]]

	Cols = RatesA.columns

	Fig = go.Figure(
		layout = {
			"xaxis_title":"Time, t",
   			"yaxis_title":"Rolling Mean Rate / day",
			"autosize":True,
			"margin" : {"l":10,"r":10,"t":10,"b":10},
			"height" : Height,
			#"xaxis_type":'log',
			"xaxis_range":XRange,
			#"yaxis_type":'log',
			"yaxis_range":YRange,
			"plot_bgcolor":'white',
			}
	)


	Fig.add_trace(
		go.Scatter(
			x=RatesA.index, y=RatesA[Label], name="",
			hoverinfo="name+x+y",
			#customdata=np.log10(Rates[Label]),
			hovertemplate= "<br>N: %s" % (Cols[0])+"<br>t: %{x}<br> y: %{y:.2f}",
			line={"width": 1, "color":"black"},
			marker={"size": 5},
			mode="lines",
			showlegend=False,
		)
	)
	

	#Highlight flagged regions
	for Ri in range(RegionsA.shape[0]):
		if RegionsA.iloc[Ri]["Duration"] <= NDur:
			continue
		Fig.add_shape( 
			fillcolor="orange",
			opacity=0.4,
			line={"width": 0},
			type="rect",
			x0=Misc.unixToDatetime(RegionsA.iloc[Ri]["Starts"]),
			x1=Misc.unixToDatetime(RegionsA.iloc[Ri]["Stops"]),
			xref="x",
			y0=YRange[0],
			y1=YRange[1],
			yref="y",
			layer='above',	
		),
	if isinstance(RegionsS, (int)):
		pass
	else:
		for Ri in range(RegionsS.shape[0]):
			if RegionsS.iloc[Ri]["Duration"] <= NDur:
				continue
			Fig.add_shape( 
				fillcolor="red",
				opacity=0.4,
				line={"width": 0},
				type="rect",
				x0=Misc.unixToDatetime(RegionsS.iloc[Ri]["Starts"]),
				x1=Misc.unixToDatetime(RegionsS.iloc[Ri]["Stops"]),
				xref="x",
				y0=YRange[0],
				y1=YRange[1],
				yref="y",
				layer='above',	
			),
		Fig.add_trace(
			go.Scatter(
				x=RatesS.index, y=RatesS[Label], name="",
				hoverinfo="name+x+y",
				#customdata=np.log10(Rates[Label]),
				hovertemplate= "<br>N: %s" % (TestCol)+"<br>t: %{x}<br> y: %{y:.2f}",
				line={"width": 1, "color":"purple"},
				marker={"size": 5},
				mode="lines",
				showlegend=False,
			)
		)

	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=Lim, x1=XRange[1], y1=Lim,
			line={
	    		"width":1,
				"color":"red",
				"dash":"dash",
			}
	)
		


	#Bounding box for double-click reset
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[1], y1=YRange[0],
			line={
	    		"width":0,
			"color":"purple",
			"dash":"dash",
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)

	#For range fixing only. (Invisable line)
	Fig.add_shape(
			type="line",
			x0=XRange[0], y0=YRange[0], x1=XRange[0], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	Fig.add_shape(
			type="line",
			x0=XRange[1], y0=YRange[0], x1=XRange[1], y1=YRange[1],
			line={
	    		"width":0,
			}
	)
	return Fig

######################
# Figures Code: Empty fig
######################

def EmptyFig(Height):
	''' Function to create an empty figure for correct proportions,
	Height: Height in pixels required. (Width autoscales)
	Returns,
	Fig: An empty figure element.'''
	Fig = go.Figure()
	Fig.update_layout(
		autosize=True,
		margin = {"l":10,"r":10,"t":10,"b":10},
		height=Height,
	)
	return Fig	
	


if __name__ == "__main__":
	print("Run as module") 
