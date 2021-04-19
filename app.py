"""============================================================================
Python Dashboard produced to monitor timeseries data with high periodicity and search for anomlous regions in the data. 

Dashboard largely developed based on tutorial located at https://realpython.com/python-dash/ and inspired by https://dash-gallery.plotly.host/dash-manufacture-spc-dashboard/.

Contents: 
- Imports and Set Up
	- Local Parameters
	- Hyperparameter Loading
	-Read In Markdown
- Functions used in callbacks
- Tabs, Graphs and Banners
- Individual tab layouts
	Tab 1: Raw variables
	Tab 2: Fourier Anaylsis
	Tab 3: Alpha Anaylsis
	Tab 4: BOCPD
	Tab 5: PCA
- Bootstrap Style sheet and run
- Layout
- Callbacks
	- Modals
	- Server time
	- Tabs
- Callbacks Tab 1:
- Callbacks Tab 2:
- Callbacks Tab 3:
- Callbacks Tab 4:
- Callbacks Tab 5:
- Cache
- Reset Folders data
- argv

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""

################################################################################################################
# Imports and Set Up
################################################################################################################

#Required Dash Libraries
#Initalization
import dash 
#Interactive components
import dash_core_components as dcc
#HTML tags
import dash_html_components as html
#Bootstrap components cols and rows
import dash_bootstrap_components as dbc
#Callback functions
from dash.dependencies import Output, Input, State

#Pandas for data import and management
import pandas as pd
import numpy as np
import scipy

#For moving data around as child
import json

#Command lines
import sys, getopt
import os
import time

#For manipulating datetime format
from datetime import datetime
from datetime import timedelta

#Import python codes for each anaylsis
from codes import DatManipulation as DatM
from codes import Fourier
from codes import BOCPD
from codes import PCA
from codes import Misc
from codes import CalcStats
#Graph code
from codes import DashPlots
from codes import Graphing
from multiprocessing import Process
#Default Parameters
import Vars

#######################
# Local Parameters
#######################

defaulttab='tab-1'

#Timing for periodic refreshes
dt_small = 1 
dt_mid = 5 
dt_big = 5

#######################
# Hyperparameter Loading
#######################

#General Dashsettings
SearchHeight = "60px"
FigHeightPX = 400

DefaultFeature =            Vars.DefaultFeature
DefaultErrSize = 		    Vars.DefaultErrSize
DefaultDataType =           Vars.DefaultDataType
DefaultRescale =            Vars.DefaultRescale
DefaultMetric =             Vars.DefaultMetric

#General Window
WindowUnit =                Vars.WindowUnit
WindowN =                   Vars.WindowN

#Alpha Hyperparameters
Alpha_MinFreq =             Vars.Alpha_MinFreq
Fourier.Alpha_MinFreq = Alpha_MinFreq

#Set DefaultParams
BOCPD_tol =                 Vars.BOCPD_tol
BOCPD_haz =                 Vars.BOCPD_haz
BOCPD_MaxSeqLength =        Vars.BOCPD_MaxSeqLength
BOCPD_errsScale =           Vars.BOCPD_errsScale

BOCPD.BOCPD_tol = BOCPD_tol
BOCPD.BOCPD_MaxSeqLength = BOCPD_MaxSeqLength
BOCPD.BOCPD_haz = BOCPD_haz

#PCA Hyperparameters
PCA_FittedParams =          Vars.PCA_FittedParams
PCA_WindowUnit = WindowUnit
PCA_WindowN = WindowN

#Rolling window
PCA.Rolling_WindowUnit =    Vars.Rolling_WindowUnit
PCA.Rolling_Window =        Vars.Rolling_Window

DatM.FileSuffix =           Vars.FileSuffix
Graphing.BOCPD_errsScale =  Vars.BOCPD_errsScale

SaveFigs =                  Vars.SaveFigs
SaveCache =                 Vars.SaveCache

#######################
# Read In Markdown
#######################

text_markdown = "\n \t"
with open('assets'+os.sep+'LoadInfo.md') as this_file:
    for a in this_file.read():
        if "\n" in a:
            text_markdown += "\n \t"
        else:
            text_markdown += a


################################################################################################################
# Functions used in callbacks
################################################################################################################

def update_dropdown_files(DataDirectory):
	'''
    Update options for dropdown listing available files,

            Parameters:
                	DataDirectory (str): directory containing files

            Returns:
                    OptionsDict (dcc.options): dropdown options
					value (dcc.value): value of dropdown
    '''
	Files = DatM.GlobDirectory(DataDirectory)
	if len(Files) != 0:
		return	[{'label':"Variable: %s" % (name), 'value':name} for name in Files], Files[0]
	else:
		return [{'label':"Variable: %s" % (name), 'value':name} for name in []], None

def DateSlider(jsonified_data):
	'''
    Return the data slider for a given data set with datetime index,

            Parameters:
                    jsonified_data (JSON): jsonified data with datatime index

            Returns:
                    Min (float): Min value on slider
					Max (float): Max value on slider
					value (list[float]): [Initial Start, Initial End] 
					marks (dict): dict of marks locations
    '''
	if jsonified_data not in [0,"0", None, "None"]:
		daterange = pd.read_json(jsonified_data, orient='split').index
		Min = Misc.unixTimeMillis(daterange.min())
		Max = Misc.unixTimeMillis(daterange.max())
		value = [Misc.unixTimeMillis(daterange.min()),Misc.unixTimeMillis(daterange.max())]
		marks = Misc.getMarksDates(daterange.min(),daterange.max(),daterange)
		return Min, Max, value , marks
	else:
		Min = 0
		Max = 10
		value = [0,10]
		marks = {}
		return Min, Max, value , marks

def LoadDataAfterDropdowns(DataDirectory, Data_i_Name, inter=False):
	'''
    Load and jsonify data to move through callbacks,

            Parameters:
                    DataDirectory (str): directory containing files
                    Data_i_Name (str): File name
					inter (bool): T/F If to run linear interpolation on missing datapoints

            Returns:
                    json (JSON): Jsonified data
    '''
	if Data_i_Name not in [None, "None"]:
		data = DatM.LoadData(DataDirectory, Data_i_Name, inter)
		return data.to_json(date_format='iso', orient='split')
	else:
		return 0

def toggle_modal(n1, n2, is_open):
	'''
    Toggle info modal displays

            Parameters:
                    n1 (bool): Is open clicked
                    n2 (bool): Is close clicked
					is_open (bool): T/F is open or closed

            Returns:
                    is_open (bool): T/F is open or closed
    '''
	if n1 or n2:
		return not is_open
	return is_open

def Intervals(RefreshRate, ID):
	'''
    Create Intervals object to fire periodically,

            Parameters:
                    RefreshRate (float): Rate for fire in seconds,
                    ID (str): Reference name,

            Returns:
                    Interval (dcc.interval): dcc.interval object
    '''
	return dcc.Interval(
			id=ID,
			#In milliseconds
			interval=RefreshRate * 1000,
			n_intervals=0,  
	)

def Spinner(ID):
	'''
    Return loading spinner object,

            Parameters:
                	ID (str): Reference name,

            Returns:
                    Div (html.Div): html.Div containing spinner object to display when loading
    '''
	return html.Div(
		dbc.Spinner(
			html.Div(id=ID), 
			size='lg',
			fullscreen=True,
			fullscreen_style={"background-color":None},
			color="#68246D",
		),
	)

def build_Process(Tab):
	'''
    Returns progress bar and run all button,

            Parameters:
                    Tab (str): Part of string defining referance ID

            Returns:
                    Div (html.Div): html.Div object containing progress bar and run button
    '''
	return html.Div(
		children = [
			html.H3(children="Run all:", id=Tab+"Process-Header" ,className="Header-text"),
			dbc.Row(
				children=[
					dbc.Col(
						html.Div(),
						width = 1,
						className="Cols",
					),
					dbc.Col(
						dbc.Button('Run All', id=Tab+'Process-Button', n_clicks=0, className="Button"),
						width = 2,
						className="Cols",
					),
					dbc.Col(
						html.Div(),
						width = 1,
						className="Cols",
					),
					dbc.Col(
						dbc.Progress("0\u0025", value=0, id=Tab+'Process-Progress', className="Progress", barClassName="ProgressBar"),
						width = 7,
						className="Cols",
					), 
					dbc.Col(
						html.Div(),
						width = 1,
						className="Cols",
					),
				],
			),
		],
		id=Tab+"Process",
	)
		
################################################################################################################
# Tabs, Graphs and Banners
################################################################################################################

def build_graph(ID, Size):
	'''
    Returns empty plotly graph placeholder

            Parameters:
                    ID (str): ID referance for this graph
                    Size (int): Pixel sixt

            Returns:
                    Div (html.Div): html.Div containing blank dcc.Graph object
    '''
	return html.Div(
		dcc.Graph(
			figure = DashPlots.EmptyFig(Size),
			id=ID, config={"displayModeBar": False, "doubleClick":"reset"},
		),
		className="graphContainer",
	)

def build_banner():
	'''
   	Return banner html.Div element framing the dashboard

            Parameters:

            Returns:
                    Div (html.Div): html.Div object containing the banner build
    '''
	return html.Div(
		id="banner",
		className="banner",
		children=[
			html.Div(
				id="banner-text",
				children=[
					html.H5("Timeseries Analysis Dashboard"),
					html.H6("A frequency analysis toolbox"),
				],
			),
			html.Div(
				id="banner-Img",
				children=[
					html.A([html.Img(src="assets"+os.sep+"durham-university-2019.png")],href="https://www.dur.ac.uk/", target='_blank'),
					
					html.A([html.Img(src="assets"+os.sep+"logo-plotly.svg")],href="https://plotly.com/dash/", target='_blank'),
				],
			),
		],
	)

def build_tabs():
	'''
    Return dcc.Tabs which define main appearance of the dashboard

            Parameters:

            Returns:
                    Div (html.Div): html.Div containing all Tabs and larger structure of dashboard 
    '''
	return html.Div(
		className="tabs",
		children = [
			dcc.Tabs(
				id='tabs',
				className="custom-tabs",
				value=defaulttab,
				children=[
					dcc.Tab(label='Variables', value='tab-1', className="custom-tab", selected_className="custom-tab--selected"),
					dcc.Tab(label='Fourier Analysis', value='tab-2', className="custom-tab", selected_className="custom-tab--selected"),
					dcc.Tab(label='Alpha Analysis', value='tab-3', className="custom-tab", selected_className="custom-tab--selected"),
					dcc.Tab(label='BOCPD', value='tab-4', className="custom-tab", selected_className="custom-tab--selected"),
					dcc.Tab(label='PCA', value='tab-5', className="custom-tab", selected_className="custom-tab--selected"),
				]
			),
		]
	)

################################################################################################################
# Individual tab layouts
################################################################################################################
#######################
# Tab 1: Raw variables
#######################

def build_rawdatasummary(Parameters):
	'''
    Return the key stats summary to left of Rawgraph figure

            Parameters:
                    Parameters (dict): dictionary of statistics over the highlighted region

            Returns:
                    Div (html.Div): Formated left column containing data.
    '''
	if Parameters["Mean"] != "N/A":
		t0 = Misc.unixToDatetime(Parameters["Start"])
		t1 = Misc.unixToDatetime(Parameters["End"])
	else:
		t0 = "N/A"
		t1 = "N/A"
	ModalText = [
		html.P(["An interactive plot showing the variables selected with the string search or dropdown menu. Place data in the data/Rawdata folder and \
		the drop-down menus will automatically display available data. The radio select 'Rescaled' will mean center the plotted data and 'None' will \
		plot in natural units. On the left section of the graph are readouts of key statistics of the highlighed region which can be adjusted using \
		the slider. Up-to 6 features can be plotted at once."],className="Header-text"),

	]
	return html.Div(
		children = [
			dbc.Modal(
				children = 	[
					dbc.ModalHeader("Raw variables info"),
					dbc.ModalBody(ModalText),
					dbc.ModalFooter(
					    dbc.Button("Close", id="RawModal-Close", className="ModalButton")
					),
			    ],
				size="lg",
				scrollable=True,
			    id="RawModal",
			),
			html.H3(["Raw variables plot"],className="Header-text"),
			html.P(["Highlighted region statistics;"],className="Header-text"),
			html.P(["t",html.Sub("0")," = %s" % (t0)],className="Para-text"),
			html.P(["t",html.Sub("1")," = %s" % (t1)],className="Para-text"),
			html.P(["t",html.Sub("0"),"-t", html.Sub("1"),"=%s days" % (Parameters["Duration"])],className="Para-text"),
			html.P(["\u0394t = %s %s" % (Parameters["Rate"], Parameters["RateUnit"])],className="Para-text"),

			html.P(["The calculated statistics;"],className="Header-text"),
			html.P(["\u00B5(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (Parameters["Mean"])],className="Para-text"),
			html.P(["\u03C3(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (Parameters["STD"])],className="Para-text"),
			html.P(["min(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (Parameters["Min"])],className="Para-text"),
			html.P(["max(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (Parameters["Max"])],className="Para-text"),
			dbc.Button(
				html.Span( html.Img(src="assets"+os.sep+"info.png", className="ButtonImg")),
				id="RawModal-Open", className="ButtonInfo"
			),
		],
		className="graphContainer",	
	)

def build_tab1(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale):
	'''
    Return the tab element of the Raw graphs tab.

            Parameters:
                    DefaultFeature (str): Default search string
					DefaultErrSize (float): Error scaling factor
					DefaultDataType (str): "Raw", "Alpha" or "BOCPD"
					DefaultRescale (float): "Norm", Plot as raw, "Rescale", plot mean centered features

            Returns:
                    Div (html.Div): Built Tab
    '''
	offset = 1
	sizegraph = 8
	TabName = "Raw"
	
	return html.Div(
			children=[
				Spinner("Spinner-tab1-A"),
				Spinner("Spinner-tab1-B"),
				Spinner("Spinner-tab1-C"),
				Spinner("Spinner-tab1-D"),
				#Placeholders
				html.Div( 
					style={'display': 'none'},
					children = [
						html.H1(
							id=TabName+'Direct',
							children="data"+os.sep+TabName+'Data',
						),
						html.H1(
							id=TabName+'Data',
							children="0",
						),
						html.H1(
							id=TabName+'DataError',
							children="0",
						),
						html.H1(
							id=TabName+'DataSummary',
							children=json.dumps(CalcStats.CalcStatsEmpty()),
						),	
					]	
				),

	
				dbc.Row(
					children = [
						#First column
						dbc.Col(
							html.Div(
								children = [
									build_rawdatasummary(CalcStats.CalcStatsEmpty())
								],
								id="RawTable",								
							),
							width=12-sizegraph,
							className = "Cols",
						),

						#Second column
						dbc.Col(
							children = [
								dbc.Row(
									children = [
										dbc.Col(
											children=[
												dcc.Dropdown(
													id=TabName+'ColName-dropdown',
													multi=True,	
													placeholder="Select a variable",	
													style = {"overflow-y":"scroll", "height":SearchHeight},			
												),
											], 
											width={"size":6, "offset": 0},
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'StrSearch',
													type="text",
													value=DefaultFeature,
													placeholder="String Search",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'SigNum',
													type="number",
													value=DefaultErrSize,
													min=0,
													placeholder="Error multiplier",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											dcc.RadioItems(
												id=TabName+'Normed',
												options=[{'label': i+"    ", 'value': i} for i in ['None','Rescaled']],
												value=DefaultRescale,
											),
											width={"size":2, "offset": 0},
											className = "Cols",
										),
									],
									className = "Rows",
								),
				
								dbc.Row(
									children = [
										build_graph("RawGraph", FigHeightPX),
									],
									className = "Rows",
								),

								dbc.Row(
										children = [
											dbc.Col(
												children=[
													html.Div()			
												], 
												width={"size":1, "offset": 0},
												className = "Cols",
											),
											dbc.Col(
												children = [
													dcc.RangeSlider(
														id=TabName+'RangeSlider',
													)	
												],
												width={"size":10, "offset": 0},
												style={"display": "inline-block", "width": "100%"},
											),
											dbc.Col(
												children=[
													html.Div()			
												], 
												width={"size":1, "offset": 0},
												className = "Cols",
											),
											],
										className = "Rows",
								
								),

								
							],
							width=sizegraph,
							className = "Cols",
						)
					]
				)
			]
	)
#######################
# Tab 2: Fourier Anaylsis
#######################

def build_fourierdatasummary(Parameters, FourierStats):
	'''
    Return the key stats summary to left of figures

            Parameters:
                    Parameters (dict): dictionary of statistics over the highlighted region about raw data
					FourierStats (dict): dictionary of statistics over the highlighted region about Fourier fit

            Returns:
                    Div (html.Div): Formated left column containing data.
    '''
	if Parameters["Mean"] != "N/A":
		t0 = Misc.unixToDatetime(Parameters["Start"])
		t1 = Misc.unixToDatetime(Parameters["End"])
	else:
		t0 = "N/A"
		t1 = "N/A"

	ModalText = [
		html.P(["This demo tab demonstrates the fast Fourier transform that is preformed for the \u03B1 analysis. The slider allows adjustments to \
		the window size and refits the transform over this region. The red line indicates the fitted power spectrum function of the form \
		A",html.Sub("0"),"f",html.Sup("\u03B1")," This \u03B1 is value associated for this window. Details of the fit and window are shown on \
		the left."],className="Header-text"),
	]
	return html.Div(
		children = [
			dbc.Modal(
				children = 	[
					dbc.ModalHeader("Fourier info"),
					dbc.ModalBody(ModalText),
					dbc.ModalFooter(
					    dbc.Button("Close", id="FourierModal-Close", className="ModalButton")
					),
			    ],
				size="lg",
				scrollable=True,
			    id="FourierModal",
			),
			html.H3(["Fourier anaylsis plots"],className="Header-text"),
			html.P(["Highlighted region statistics;"],className="Header-text"),
			html.P(["t",html.Sub("0")," = %s" % (t0)],className="Para-text"),
			html.P(["t",html.Sub("1")," = %s" % (t1)],className="Para-text"),
			html.P(["t",html.Sub("0"),"-t", html.Sub("1"),"=%s days" % (Parameters["Duration"])],className="Para-text"),
			html.P(["\u0394t = %s %s" % (Parameters["Rate"],Parameters["RateUnit"])],className="Para-text"),

			html.P(["Fit parameters;"],className="Header-text"),
			html.P(["A",html.Sub("0"), "(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s \u00B1 %s" % (FourierStats["A0"],FourierStats["A0Err"])],className="Para-text"),
			html.P(["\u03B1(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s \u00B1 %s" % (FourierStats["Alpha"],FourierStats["AlphaErr"])],className="Para-text"),
			dbc.Button(
				html.Span( html.Img(src="assets"+os.sep+"info.png", className="ButtonImg")),
				id="FourierModal-Open", className="ButtonInfo"
			),
			
		],
		className="graphContainer",	
	)

def build_tab2(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale):
	'''
    Return the tab element of the Fourier graphs tab.

            Parameters:
                    DefaultFeature (str): Default search string
					DefaultErrSize (float): Error scaling factor
					DefaultDataType (str): "Raw", "Alpha" or "BOCPD"
					DefaultRescale (float): "Norm", Plot as raw, "Rescale", plot mean centered features

            Returns:
                    Div (html.Div): Built Tab
    '''
	offset = 1
	sizegraph = 8
	TabName = "Fourier"
	
	return html.Div(
			children=[
				Spinner("Spinner-tab2-A"),
				Spinner("Spinner-tab2-B"),
				Spinner("Spinner-tab2-C"),
				Spinner("Spinner-tab2-D"),
				#Placeholders
				html.Div( 
					style={'display': 'none'},
					children = [
						html.H1(
							id='RawDirect',
							children="data"+os.sep+"RawData",
						),
						html.H1(
							id=TabName+'Data',
							children="0",
						),
						html.H1(
							id=TabName+'DataSummary',
							children=json.dumps(CalcStats.CalcStatsEmpty()),
						),
						html.H1(
							id=TabName+'FourierDataSummary',
							children=json.dumps(CalcStats.CalcFourierStatsEmpty()),
						),
					]
				),
	
				dbc.Row(
					children = [
						#First column
						dbc.Col(
							html.Div(
								children = [
									build_fourierdatasummary(CalcStats.CalcStatsEmpty(),CalcStats.CalcFourierStatsEmpty())
								],
								id="FourierTable",
								
							),
							width=12-sizegraph,
							className = "Cols",
						),

						#Second column
						dbc.Col(
							children = [
								dbc.Row(
									children = [
										dbc.Col(
											children=[
												dcc.Dropdown(
													id=TabName+'ColName-dropdown',
													multi=False,	
													placeholder="Select a variable",	
													style = {"overflow-y":"scroll", "height":SearchHeight},			
												),
											], 
											width={"size":6, "offset": 0},
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'StrSearch',
													type="text",
													value=DefaultFeature,
													placeholder="String Search",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'SigNum',
													type="number",
													value=DefaultErrSize,
													min=0,
													placeholder="Error multiplier",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											dcc.RadioItems(
												id=TabName+'LinLog',
												options=[{'label': i+"    ", 'value': i} for i in ['Linear', 'Log']],
												value='Log',
												labelStyle={'display': 'inline'}
											),
											width={"size":2, "offset": 0},
											className = "Cols",
										),
									
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("FourierGraph", FigHeightPX/2),
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("FourierRawGraph", FigHeightPX/2),
									],
									className = "Rows",
								),

								dbc.Row(
										children = [
											dbc.Col(
												children=[
													html.Div()			
												], 
												width={"size":1, "offset": 0},
												className = "Cols",
											),
											dbc.Col(
												children = [
													dcc.RangeSlider(
														id=TabName+'RangeSlider',
													)	
												],
												width={"size":10, "offset": 0},
												style={"display": "inline-block", "width": "100%"},
											),
											dbc.Col(
												children=[
													html.Div()			
												], 
												width={"size":1, "offset": 0},
												className = "Cols",
											),
											],
										className = "Rows",
								
								),

							],
							width=sizegraph,
							className = "Cols",
						)
					]
				)
			]
	)

#######################
# Tab 3: Alpha Anaylsis
#######################

def build_Alphasdatasummary(Parameters, AlphaParameters):
	'''
    Return the key stats summary to left of figures

            Parameters:
                    Parameters (dict): dictionary of statistics over the highlighted region about raw data
					AlphaParameters (dict): dictionary of statistics over the highlighted region about alpha fit

            Returns:
                    Div (html.Div): Formated left column containing data.
    '''
	if Parameters["Mean"] != "N/A":
		t0 = Misc.unixToDatetime(Parameters["Start"])
		t1 = Misc.unixToDatetime(Parameters["End"])
	else:
		t0 = "N/A"
		t1 = "N/A"

	ModalText = [
		html.P(["This tab displays and performs the \u03B1 anaylsis. Use the string search and dropdown menu to select a series then click run. \
		The lower plot displays the orginal feature, the upper the \u03B1 series. Click on a data point in the top to display the fourier window below. \
		Clicking run in the lower left corner will run the anaylsis for all files in data\RawData and save them in data\AlphaData. The progess bar \
		updates while this is running."],className="Header-text"),
	]

	return html.Div(
		children = [
			dbc.Modal(
				children = 	[
					dbc.ModalHeader("Alpha anaylsis info"),
					dbc.ModalBody(ModalText),
					dbc.ModalFooter(
					    dbc.Button("Close", id="AlphasModal-Close", className="ModalButton")
					),
			    ],
				size="lg",
				scrollable=True,
			    id="AlphasModal",
			),
			html.P(["Highlighted region statistics;"],className="Header-text"),
			html.P(["t",html.Sub("0")," = %s" % (t0)],className="Para-text"),
			html.P(["t",html.Sub("1")," = %s" % (t1)],className="Para-text"),
			html.H3(["Alpha window anaylsis plots"],className="Header-text"),
			html.P(["Alpha statistics;"],className="Header-text"),
			html.P(["\u00B5(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (AlphaParameters["Mean"])],className="Para-text"),
			html.P(["\u03C3(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (AlphaParameters["STD"])],className="Para-text"),
			html.P(["min(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (AlphaParameters["Min"])],className="Para-text"),
			html.P(["max(x[t",html.Sub("0"),":t",html.Sub("1"),"]) = %s" % (AlphaParameters["Max"])],className="Para-text"),
			
		dbc.Button(
				html.Span( html.Img(src="assets"+os.sep+"info.png", className="ButtonImg")),
				id="AlphasModal-Open", className="ButtonInfo"
			),		
		],
		id="AlphasTable",
	)

def build_tab3(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale):
	'''
    Return the tab element of the Alpha graphs tab.

            Parameters:
                    DefaultFeature (str): Default search string
					DefaultErrSize (float): Error scaling factor
					DefaultDataType (str): "Raw", "Alpha" or "BOCPD"
					DefaultRescale (float): "Norm", Plot as raw, "Rescale", plot mean centered features

            Returns:
                    Div (html.Div): Built Tab
    '''
	offset = 1
	sizegraph = 8
	TabName = "Alphas"
	
	return html.Div(
			children=[
				Spinner("Spinner-tab3-A"),
				Spinner("Spinner-tab3-B"),
				Spinner("Spinner-tab3-C"),
				Spinner("Spinner-tab3-D"),
				#Placeholders
				html.Div( 
					style={'display': 'none'},
					children = [
						html.H1(
							id="RawDirect",
							children='data'+os.sep+'RawData',
						),	
						html.H1(
							id="AlphasDirect",
							children='data'+os.sep+'AlphaData',
						),	
						html.H1(
							id='AlphasRawData',
							children="0",
						),
						html.H1(
							id=TabName+'Data',
							children="0",
						),
						html.H1(
							id=TabName+'DataSummary',
							children=json.dumps(CalcStats.CalcStatsEmpty()),
						),
						html.H1(
							id=TabName+'AlphasDataSummary',
							children=json.dumps(CalcStats.CalcAlphaStatsEmpty()),
						),	
					]
				),
					
				dbc.Row(
					children = [
						#First column
						dbc.Col(
							children = [
								dbc.Row(
									build_Alphasdatasummary(CalcStats.CalcStatsEmpty(), CalcStats.CalcAlphaStatsEmpty()),
									className="graphContainer",	
									
								),
								dbc.Row(
									build_Process("Alphas"),
									className="graphContainer",
								),
							],
							width=12-sizegraph,
							className = "Cols",
						),

						#Second column
						dbc.Col(
							children = [
								dbc.Row(
									children = [
										dbc.Col(
											children=[
												dcc.Dropdown(
													id=TabName+'ColName-dropdown',
													multi=False,	
													placeholder="Select a variable",	
													style = {"overflow-y":"scroll", "height":SearchHeight},			
												),
											], 
											width={"size":6, "offset": 0},
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'StrSearch',
													type="text",
													value=DefaultFeature,
													placeholder="String Search",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'SigNum',
													type="number",
													value=DefaultErrSize,
													min=0,
													placeholder="Error multiplier",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											children=[
												dbc.Button(
													id=TabName+'Run',
													className="Button",
													children="Run",
													style={"width":"80px"},
												),
											], 
											width={"size":1, "offset": 0},											
											className = "Cols",
										),	
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("AlphasGraph", FigHeightPX/2),
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("AlphasRawGraph", FigHeightPX/2),
									],
									className = "Rows",
								),
							],
							width=sizegraph,
							className = "Cols",
						)
					], className= "Rows"
				),
			]
	)

#######################
# Tab 4: BOCPD
#######################

def build_BOCPDdatasummary(Parameters, BOCPDStats):
	'''
    Return the key stats summary to left of figures

            Parameters:
                    Parameters (dict): dictionary of statistics over the highlighted region about raw data
					BOCPDStats (dict): dictionary of statistics over the highlighted region about BOCPD

            Returns:
                    Div (html.Div): Formated left column containing data.
    '''
	if Parameters["Mean"] != "N/A":
		t0 = Misc.unixToDatetime(Parameters["Start"])
		t1 = Misc.unixToDatetime(Parameters["End"])
	else:
		t0 = "N/A"
		t1 = "N/A"

	ModalText = [
		html.P(["Bayesian Online Change Point detection. A probabilistic analysis on a live sequence of data which returns a likely-hood that points belong to the previous sequence of points given a prior. Here we've assumed a Gaussian prior with an errors scaled up-to %s sigma. The colour map is scaled logarithmically, hovering over the graph will show the sequence length and likely-hood. The red line show's the most likely sequence length, clicking will highlight the lower plot to show the data contained in this sequence. Select the single feature using the dropdown menu and click run. Alternatively click run in the lower section to run on all files in data\RawData and files will save in data\BOCPDdata." % BOCPD_errsScale],className="Header-text"),
	]
	return html.Div(
		children = [
			dbc.Modal(
				children = 	[
					dbc.ModalHeader("BOCPD info"),
					dbc.ModalBody(ModalText),
					dbc.ModalFooter(
					    dbc.Button("Close", id="BOCPDModal-Close", className="ModalButton")
					),
			    ],
				size="lg",
				scrollable=True,
			    id="BOCPDModal",
			),
			html.H3(["BOCPD anaylsis plots"],className="Header-text"),
			html.P(["Highlighted region statistics;"],className="Header-text"),
			html.P(["t",html.Sub("0")," = %s" % (t0)],className="Para-text"),
			html.P(["t",html.Sub("1")," = %s" % (t1)],className="Para-text"),
			html.P(["t",html.Sub("0"),"-t", html.Sub("1"),"=%s days" % (Parameters["Duration"])],className="Para-text"),
	
			html.P(["BOCPD overview"], className="Header-text"),
			html.P(["max(l) = %s" % (BOCPDStats["MaxSeq"])],className="Para-text"),
			html.P(["\u00B5(l) = %s" % (BOCPDStats["MeanSeq"])],className="Para-text"),
			html.P(["N(l=0) = %s" % (BOCPDStats["NoZeros"])],className="Para-text"),

			dbc.Button(
				html.Span( html.Img(src="assets"+os.sep+"info.png", className="ButtonImg")),
				id="BOCPDModal-Open", className="ButtonInfo"
			),
			
		],
		id="BOCPDTable",
	)

def build_tab4(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale):
	'''
    Return the tab element of the BOCPD graphs tab.

            Parameters:
                    DefaultFeature (str): Default search string
					DefaultErrSize (float): Error scaling factor
					DefaultDataType (str): "Raw", "Alpha" or "BOCPD"
					DefaultRescale (float): "Norm", Plot as raw, "Rescale", plot mean centered features

            Returns:
                    Div (html.Div): Built Tab
    '''
	offset = 1
	sizegraph = 8
	TabName = "BOCPD"
	
	return html.Div(
			children=[
				Spinner("Spinner-tab4-A"),
				Spinner("Spinner-tab4-B"),
				Spinner("Spinner-tab4-C"),
				Spinner("Spinner-tab4-D"),
				#Placeholders
				html.Div( 
					style={'display': 'none'},
					children = [
						html.H1(
							id="RawDirect",
							children='data'+os.sep+'RawData',
						),
						html.H1(
							id="BOCPDDirect",
							children='data'+os.sep+'BOCPDData',
						),
						html.H1(
							id=TabName+'RawData',
							children="0",
						),
						html.H1(
							id=TabName+'Data',
							children="0",
						),	
						html.H1(
							id=TabName+'DataSummary',
							children=json.dumps(CalcStats.CalcStatsEmpty()),
						),
						html.H1(
							id=TabName+'BOCPDDataSummary',
							children=json.dumps(CalcStats.CalcBOCPDStatsEmpty())
						),	
					],
				),

	
				dbc.Row(
					children = [
						#First column
						dbc.Col(
							children = [
								dbc.Row(
									build_BOCPDdatasummary(CalcStats.CalcStatsEmpty(), CalcStats.CalcBOCPDStatsEmpty()),
									className="graphContainer",	
									
								),
								dbc.Row(
									build_Process("BOCPD"),
									className="graphContainer",
								),
							],
							width=12-sizegraph,
							className = "Cols",
						),

						#Second column
						dbc.Col(
							children = [
								dbc.Row(
									children = [
										dbc.Col(
											children=[
												dcc.Dropdown(
													id=TabName+'ColName-dropdown',
													multi=False,	
													placeholder="Select a variable",	
													style = {"overflow-y":"scroll", "height":SearchHeight},			
												),
											], 
											width={"size":6, "offset": 0},
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'StrSearch',
													type="text",
													value=DefaultFeature,
													placeholder="String Search",
													style={'width': "100px"},
												),
											], 
											width={"size":1, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											children=[
												html.Div()			
											], 
											width={"size":3, "offset": 0},
											className = "Cols",
										),									
										dbc.Col(
											children=[
												dbc.Button(
													id=TabName+'Run',
													className="Button",
													children="Run",
													style={"width":"80px"},
												),
											], 
											width={"size":1, "offset": 0},											
											className = "Cols",
										),
										

									
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("BOCPDGraph", FigHeightPX/2),
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("BOCPDRawGraph", FigHeightPX/2),
									],
									className = "Rows",
								),
							],
							width=sizegraph,
							className = "Cols",
						)
					], className = "Rows",
				)
			]
	)

#######################
# Tab 5: PCA
#######################

def build_PCAdatasummary(Parameters, PCAStats):
	'''
    Return the key stats summary to left of figures

            Parameters:
                    Parameters (dict): dictionary of statistics over the highlighted region about raw data
					PCAStats (dict): dictionary of statistics over the highlighted region about PCA fit

            Returns:
                    Div (html.Div): Formated left column containing data.
    '''
	if Parameters["Mean"] != "N/A":
		t0 = Misc.unixToDatetime(Parameters["Start"])
		t1 = Misc.unixToDatetime(Parameters["End"])
	else:
		t0 = "N/A"
		t1 = "N/A"

	ModalText = [
		html.P(["Select the desired features using the string search or dropdown menu. A rolling PCA window has been deployed to calculate two key \
		statistics. The T squared statistic, a metric of how well fitted the PCA model is to the new data point and the Q statistic a metric of how well \
		understood the residuals are to the model. Both of which are good indicators of anomalies. Any values exceeding a confidence limit on the model \
		will be flaged (yellow) and these contribute to the rolling rate which is plotted in the top plot. The bottom plot shows the PCA transformed \
		features. A dropdown menu at the bottom will plot one of the features alone and it's marginalised rate. Key statistics \
		are displayed on the left."],className="Header-text"),
	]
	return html.Div([
			dbc.Modal(
				children = 	[
					dbc.ModalHeader("PCA info"),
					dbc.ModalBody(ModalText),
					dbc.ModalFooter(
					    dbc.Button("Close", id="PCAModal-Close", className="ModalButton")
					),
			    ],
				size="lg",
				scrollable=True,
				id="PCAModal",
			),
			html.H3(["PCA anaylsis plots"],className="Header-text"),
			html.P(["Highlighted region statistics;"],className="Header-text"),
			html.P(["t",html.Sub("0")," = %s" % (t0)],className="Para-text"),
			html.P(["t",html.Sub("1")," = %s" % (t1)],className="Para-text"),
			html.P(["t",html.Sub("0"),"-t", html.Sub("1"),"=%s days" % (Parameters["Duration"])],className="Para-text"),
	
			html.P(["PCA overview"], className="Header-text"),
			html.P(["NPCA = %s" % (PCAStats["NPCA"])],className="Para-text"),
			html.P(["NRisk = %s" % (PCAStats["NRegions"])],className="Para-text"),
			html.P(["\u00B5(\u03BB",html.Sub(":NPCA"),") = %s" % (PCAStats["VarianceFracs"])],className="Para-text"),
			html.P(["\u00B5(T",html.Sup("2"),") = %s" % (PCAStats["TsMean"])],className="Para-text"),
			html.P(["\u00B5(Q) = %s" % (PCAStats["QsMean"])],className="Para-text"),
			dbc.Button(
				html.Span( html.Img(src="assets"+os.sep+"info.png", className="ButtonImg")),
				id="PCAModal-Open", className="ButtonInfo"
			),
			
		],
		id="PCATable",
	)

def build_tab5(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale):
	'''
    Return the tab element of the PCA graphs tab.

            Parameters:
                    DefaultFeature (str): Default search string
					DefaultErrSize (float): Error scaling factor
					DefaultDataType (str): "Raw", "Alpha" or "BOCPD"
					DefaultRescale (float): "Norm", Plot as raw, "Rescale", plot mean centered features

            Returns:
                    Div (html.Div): Built Tab
    '''
	offset = 1
	sizegraph = 8
	TabName = "PCA"
	
	return html.Div(
			children=[
				Spinner("Spinner-tab5-A"),
				Spinner("Spinner-tab5-B"),
				Spinner("Spinner-tab5-C"),
				Spinner("Spinner-tab5-D"),
				#Placeholders
				html.Div( 
					style={'display': 'none'},
					children = [
						html.H1(
							id="RawDirect",
							children='data'+os.sep+'RawData',
						),	
						html.H1(
							id=TabName+'RawData',
							children="0",
						),
						html.H1(
							id=TabName+'Data',
							children="0",
						),
						html.H1(
							id=TabName+'TsData',
							children="0",
						),
						html.H1(
							id=TabName+'QsData',
							children="0",
						),
						html.H1(
							id='DataSummary',
							children=json.dumps(CalcStats.CalcStatsEmpty()),
						),
						html.H1(
							id=TabName+'DataSummary',
							children=json.dumps(CalcStats.CalcPCAStatsEmpty())
						),			
					],
				),

				dbc.Row(
					children = [
						#First column
						dbc.Col(
							children = [
								dbc.Row(
									build_PCAdatasummary(CalcStats.CalcStatsEmpty(), CalcStats.CalcPCAStatsEmpty()),
									className="graphContainer",	
								),
							],
							width=12-sizegraph,
							className = "Cols",
						),

						#Second column
						dbc.Col(
							children = [
								dbc.Row(
									children = [
										dbc.Col(
											children=[
												html.Div()			
											], 
											width={"size":0, "offset": 0},
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Dropdown(
													id=TabName+'ColName-dropdown',
													multi=True,	
													placeholder="Select a variable",	
													style = {"overflow-y":"scroll", "height":SearchHeight},					
												), 
											], 
											width={"size":6, "offset": 0},
											className = "Cols",
										),
										dbc.Col(
											children=[
												dcc.Input(
													id=TabName+'StrSearch',
													type="text",
													value=DefaultFeature,
													placeholder="String Search",
													style={'width': "100px"},
												),
											], 
											width={"size":2, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											dcc.RadioItems(
												id=TabName+'TypeSelect',
												options=[
														{'label': 'Raw ', 'value': 'Raw'},
														{'label': 'Alpha ', 'value': 'Alpha'},
														{'label': 'BOCPD ', 'value': 'BOCPD'},
												],
												value=DefaultDataType,
												labelStyle={'display': 'inline'}
											),
											width={"size":2, "offset": 0},
											className = "Cols",
										),											
										dbc.Col(
											children=[
												dbc.Button(
													id=TabName+'Run',
													className="Button",
													children="Run",
													style={"width":"80px"},
												),
											], 
											width={"size":1, "offset": 0},											
											className = "Cols",
										),
										dbc.Col(
											children=[
												html.Div()			
											], 
											width={"size":1, "offset": 0},
											className = "Cols",
										),
									
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("RatesGraph", int(2*FigHeightPX/3)),
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
										build_graph("PCAGraph", int(FigHeightPX/3))
									],
									className = "Rows",
								),

								dbc.Row(
									children = [
											dbc.Col(
												children=[
													html.Div()			
												], 
												width={"size":1, "offset": 0},
												className = "Cols",
											),
											dbc.Col(
												children=[
													dcc.Dropdown(
														id=TabName+'TestFeature-dropdown',
														multi=False,	
														placeholder="Select a marginal variable",					
													), 
												], 
												width={"size":10, "offset": 0},
												className = "Cols",
											),
											dbc.Col(
												children=[
													html.Div()			
												], 
												width={"size":1, "offset": 0},
												className = "Cols",
											),
									],className = "Rows",
								),

							],
							width=sizegraph,
							className = "Cols",
						)
					], className = "Rows",
				)
			]
	)
################################################################################################################
# Bootstrap Style sheet and run.
################################################################################################################

external_stylesheets = [
    {
        "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
        "rel": "stylesheet",
    },
]
external_scripts=[]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)
app.title = "Dashboard Analysis"

################################################################################################################
# Layout
################################################################################################################

app.layout = html.Div(
	#The main part of the code defining the application dashboard calling all the individual elements.
	id="big-app-container",
	className="big-app-container",
	children=[
		#Initial info splash screen
		dbc.Modal(
				children = 	[
					dbc.ModalBody(dcc.Markdown(text_markdown)),
					dbc.ModalFooter(
					    dbc.Button("Close", id="DashboardModal-Close", className="ModalButton")
					),
			    ],
				is_open = True,
				scrollable=True,
				id="DashboardModal",
				size="xl",
				className="Modal",
			),
		#Banner
		build_banner(),
		#Refresh every second
		Intervals(dt_small, "intervalSmall"),
		Intervals(dt_mid, "intervalMid"),
		Intervals(dt_big, "intervalBig"),
		#General placeholder values
		html.Div( 
					children = [
						html.H1(
							children=0,
							id="JSON_Cache_Output",
						),
						dbc.Button(
							children=0,
							id="DashboardModal-Open",
						),
					],
					style={'display': 'none'},
		),			
		#Tab elements
		html.Div(
			html.Div(
				id="app-container",className="app-container",
				children=[
					Spinner("Spinner-tabs"),
					build_tabs(),
					html.Div(id='tabs-content'),
				],
			), className="box",
		),
		#Runtime 
		html.H5(children = ["Total runtime: %02dh:%02dm:%02ds' % (0,0,0)"], id="RuntimePrint", style = { 'color':'black'}),
	]
)

################################################################################################################
# Callbacks
################################################################################################################

#######################
# Modals
#######################
#Dashboard info screen 
app.callback(
    Output("DashboardModal", "is_open"),
    [Input("DashboardModal-Open", "n_clicks"), Input("DashboardModal-Close", "n_clicks")],
    [State("DashboardModal", "is_open")]
)(toggle_modal)

#Raw info screen
app.callback(
    Output("RawModal", "is_open"),
    [Input("RawModal-Open", "n_clicks"), Input("RawModal-Close", "n_clicks")],
    [State("RawModal", "is_open")]
)(toggle_modal)

#Fourier info screen
app.callback(
    Output("FourierModal", "is_open"),
    [Input("FourierModal-Open", "n_clicks"), Input("FourierModal-Close", "n_clicks")],
    [State("FourierModal", "is_open")]
)(toggle_modal)

#Alphas info screen
app.callback(
    Output("AlphasModal", "is_open"),
    [Input("AlphasModal-Open", "n_clicks"), Input("AlphasModal-Close", "n_clicks")],
    [State("AlphasModal", "is_open")]
)(toggle_modal)

#BOCPD info screen
app.callback(
    Output("BOCPDModal", "is_open"),
    [Input("BOCPDModal-Open", "n_clicks"), Input("BOCPDModal-Close", "n_clicks")],
    [State("BOCPDModal", "is_open")]
)(toggle_modal)

#PCA info screen
app.callback(
    Output("PCAModal", "is_open"),
    [Input("PCAModal-Open", "n_clicks"), Input("PCAModal-Close", "n_clicks")],
    [State("PCAModal", "is_open")]
)(toggle_modal)

#######################
# Server time
#######################

@app.callback(Output("RuntimePrint", 'children'),
	[Input('intervalSmall', 'n_intervals'),Input('intervalSmall', 'interval')])
def update_runtime(timetot, interval):
	'''
    Displays local server connection runtime

            Parameters:
                    timetot (float): runtime in seconds
                    interval (float): interval pulse duration

            Returns:
                    Time (str): Run time in formatted string
    '''
	timetot = timetot * (interval/1000)
	m, s = divmod(timetot, 60)
	h, m = divmod(m, 60)    
	return 'Total runtime: %02dh:%02dm:%02ds' % (h,m,s)

#######################
# Tabs
#######################

# Update tab selection.
@app.callback([Output('tabs-content', 'children'),Output("Spinner-tabs", "children")],
              [Input('tabs', 'value')],
)
def render_tab_content(tab):
	'''
    Update rendered tab

            Parameters:
                    tab (string): tab ID tab-x

            Returns:
                    Div (html.Div): html.Div of build tab
    '''
	if tab == 'tab-1':
		return build_tab1(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale), ""

	elif tab == 'tab-2':
		return build_tab2(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale), ""

	elif tab == 'tab-3':
		return build_tab3(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale), ""

	elif tab == 'tab-4':
		return build_tab4(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale), ""

	elif tab == 'tab-5':
		return build_tab5(DefaultFeature, DefaultErrSize, DefaultDataType, DefaultRescale), ""

################################################################################################################
# Callbacks Tab 1:
################################################################################################################

#######################
# Dropdowns
#######################

@app.callback(
	[Output('RawColName-dropdown','options'),Output('RawColName-dropdown','value')],
	[Input('RawStrSearch', "value")],
	[State('RawDirect','children')],
	)
def update_dropdowns(StrSearch, RawDir):
	'''
    Update options for dropdown element for variables in Raw graphs

            Parameters:
                    StrSearch (float): Key substring to index files by
                    RawDir (float): Files directory

            Returns:
                    Dropdowns (options): List of possible dropdowns
					Value (value): Initial selected value
    '''
	Files = DatM.GlobDirectory(RawDir)
	KeySelected = Misc.PatternsList(StrSearch, Files)
	if len(KeySelected) > 0:
		Value = KeySelected
	else:
		KeySelected = Files
		Value = None

	global DefaultFeature
	DefaultFeature = StrSearch
	
	return [{'label':"Variable: %s" % (name), 'value':name} for name in KeySelected], Value

#######################
# Sliders
#######################

app.callback(
	[Output('RawRangeSlider','min'),Output('RawRangeSlider','max'),Output('RawRangeSlider','value'),Output('RawRangeSlider','marks')],
	[Input('RawData','children')]
)(DateSlider)

#######################
# Load Data
#######################

@app.callback(
	[Output('RawData', 'children'),Output('RawDataError', 'children')],
	[Input('RawDirect','children'), Input('RawColName-dropdown', 'value')],
	)
def update_data(RawDir, Features):
	'''
    Update raw graph data

            Parameters:
                    RawDir (float): Files directory
					Features (list): List of features to be loaded

            Returns:
                    data (json): Jsonified data
					error (json): Jsonified errors
    '''
	if Features not in [None, "None"]:
		if len(Features) > 6:
			return 0,0
		data, err = DatM.PCALOAD(RawDir, Features)
		if data.empty: #Checks to make sure senible to plot
			return 0,0
		return data.to_json(date_format='iso', orient='split'), err.to_json(date_format='iso', orient='split')
	else:
		return 0,0

#######################
# Raw Plots
#######################

@app.callback(
	[Output('RawGraph', 'figure'),Output("RawDataSummary","children")],
	[Input('RawData','children'), Input('RawDataError', 'children'), Input('RawRangeSlider','value'), Input("RawSigNum","value"), Input("RawNormed","value")]
	)
def update_graph(jsonified_data,jsonified_err,value, sig, Norm):
	'''
    Update raw graph selected

            Parameters:
                    jsonified_data (json): Jsonified data
					jsonified_error (json): Jsonified errors
					value ([float,float]): Slider positions
					sig (float): Error scaling factor
					Norm (str): "Norm" or "Rescaled". If to mean center plots

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
                    
    '''
	global DefaultRescale
	DefaultRescale = Norm

	if jsonified_data not in [0,"0", None, "None"]:
		startval = Misc.unixToDatetime(value[0])
		endval = Misc.unixToDatetime(value[1]+1)
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		err = pd.read_json(jsonified_err, orient='split')
		#Remove Timezone info that read_json puts in

		data.index = data.index.tz_localize(None) 
		err.index = data.index.tz_localize(None) 

		Data_i_Name = data.columns[0]
		
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[startval:endval])

		if Norm == "None":
			Fig = DashPlots.CreateRawFigStacked(data, err, sig, data.columns, WindowParameters, FigHeightPX)
		if Norm == "Rescaled":
			Fig = DashPlots.CreateRawFigStacked(data.transform(lambda x: x-x.mean()), err, sig, data.columns, WindowParameters, FigHeightPX)
	
		if SaveFigs == 1:
			XRange = [data.index[0],data.index[-1]]
			YRange = [None,None]
			NameDate =  "_%s_%s" % (XRange[0].strftime("%d%m%Y"),XRange[1].strftime("%d%m%Y"))
			p1 = Process(target=Graphing.plotMATPLOTLIB, args=[[data.index],[data[Data_i_Name].values], [None],XRange,YRange,"linear", "linear", [], [], "Time, t", Data_i_Name, [""], ["black"],["-"],"cachefiles"+os.sep+"Raw",Data_i_Name+NameDate,True])
			p1.start()
			p1.join()
		return Fig, json.dumps(WindowParameters)
	else:
		return DashPlots.EmptyFig(FigHeightPX), json.dumps(CalcStats.CalcStatsEmpty())

#######################
# Summary Stats
#######################

@app.callback(
	Output('RawTable', 'children'),
	[Input("RawDataSummary","children")]
	)
def update_Summary(Parameters):
	'''
    Load paramters into summary column

            Parameters:
                    Parameters (json): Parameters summarising Raw data

            Returns:
                    Dict (dict): Parameters summarising Raw data
    '''
	Parameters = json.loads(Parameters)
	return build_rawdatasummary(Parameters)
	
################################################################################################################
# Callbacks Tab 2:
################################################################################################################

#######################
# Dropdowns
#######################

@app.callback(
	[Output('FourierColName-dropdown','options'),Output('FourierColName-dropdown','value')],
	[Input('FourierStrSearch', "value")],
	[State('RawDirect','children')],
	)
def update_dropdowns(StrSearch, RawDir):
	'''
    Update options for dropdown element for variables in Raw graphs

            Parameters:
                    StrSearch (float): Key substring to index files by
                    RawDir (float): Files directory

            Returns:
                    Dropdowns (options): List of possible dropdowns
					Value (value): Initial selected value
    '''
	Files = DatM.GlobDirectory(RawDir)
	KeySelected = Misc.PatternsList(StrSearch, Files)
	if len(KeySelected) > 0:
		Value = KeySelected[0]
	else:
		KeySelected = Files
		Value = None

	global DefaultFeature
	DefaultFeature = StrSearch

	return [{'label':"Variable: %s" % (name), 'value':name} for name in KeySelected], Value

#######################
# Sliders
#######################

app.callback(	[Output('FourierRangeSlider','min'),Output('FourierRangeSlider','max'),Output('FourierRangeSlider','value'),Output('FourierRangeSlider','marks')],
	[Input('FourierData','children')]
)(DateSlider)

#######################
# Update data
#######################

app.callback(
	Output('FourierData', 'children'),
	[Input('RawDirect','children'), Input('FourierColName-dropdown', 'value')]
)(LoadDataAfterDropdowns)

#######################
# Raw Plots
#######################

@app.callback(
	[Output('FourierRawGraph', 'figure'),Output("FourierDataSummary","children")],
	[Input('FourierData','children'), Input('FourierRangeSlider','value'),Input("FourierSigNum", "value")],
	)
def update_graph(jsonified_data, value, sig):
	'''
    Update Fourier Raw graph

            Parameters:
                    jsonified_data (json): Jsonified data
					value ([float,float]): Slider positions
					sig (float): Error scaling factor

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
                    
    '''
	if jsonified_data not in [0,"0", None, "None"]:
		startval = Misc.unixToDatetime(value[0])
		endval = Misc.unixToDatetime(value[1])
		
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		#Remove Timezone info that read_json puts in
		data.index = data.index.tz_localize(None) 

		Data_i_Name = data.columns[0]
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[startval:endval][Data_i_Name])
		FigRaw = DashPlots.CreateRawFig(data, sig, Data_i_Name, WindowParameters, FigHeightPX/2)
		return FigRaw, json.dumps(WindowParameters)
	else:
		return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcStatsEmpty())

@app.callback(
	[Output('FourierGraph', 'figure'),Output("FourierFourierDataSummary","children")],
	[Input('FourierData','children'), Input('FourierRangeSlider','value'), Input("FourierLinLog","value")],
	[State("FourierSigNum", "value")]
	)
def update_graph(jsonified_data, value, LinLog, sig):
	'''
    Update Fourier graph

            Parameters:
                    jsonified_data (json): Jsonified data
					value ([float,float]): Slider positions
					LinLog (str): "Linear" or "Log" scaling on power spectrum
					sig (float): Error scaling factor

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
                    
    '''
	if jsonified_data not in [0,"0", None, "None"]:
		startval = Misc.unixToDatetime(value[0])
		endval = Misc.unixToDatetime(value[1])
		
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		#Remove Timezone info that read_json puts in
		data.index = data.index.tz_localize(None) 

		Data_i_Name = data.columns[0]
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[startval:endval][Data_i_Name])
		units = Misc.CalcUnits(WindowParameters["Rate"],WindowParameters["RateUnit"])
		if units == None:
			return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcFourierStatsEmpty())
		fftfreq, AmpSpec, _ = Fourier.FourierTransform(data[Data_i_Name].values, units)

		if LinLog == 'Log':
			MinValue = min(AmpSpec[fftfreq > 0])/10
			MaxValue = max(AmpSpec[fftfreq > 0])*10
		if LinLog == 'Linear':
			MaxValue = max(AmpSpec[fftfreq > 0])*2
			MinValue = 0
		
		fftfreq, AmpSpec, Series_phase = Fourier.FourierTransform(data[startval:endval][Data_i_Name].values, units)
		
		#Error estimated on mean devition beween points
		errs = Misc.errCalculation(data, WindowParameters["RateUnit"], True)	
		PPink, PPinkErrs = Fourier.FitPink(fftfreq[fftfreq > Alpha_MinFreq], AmpSpec[fftfreq > Alpha_MinFreq], errs, units)

		FigAlpha = DashPlots.CreateFFTFig(fftfreq[fftfreq > 0], AmpSpec[fftfreq > 0],PPink, FigHeightPX/2,[MinValue, MaxValue], Alpha_MinFreq, LinLog, Data_i_Name)

		FourierStats = CalcStats.CalcFourierStats(fftfreq[fftfreq > 0], AmpSpec[fftfreq > 0],PPink, PPinkErrs) 

		if SaveFigs == 1:
			NameDate =  "_%s_%s" % (data.index[0].strftime("%d%m%Y"),data.index[-1].strftime("%d%m%Y"))
			LinesVert=[365,365*2,365*3,365*4,365*5,365*6,365*7,365*8,365*9,365*10,365*11,365*12]

			if LinLog == "Linear":
				YScale = 'linear'
			if LinLog == "Log":
				YScale = 'log'

			XRange = [fftfreq[fftfreq > 0][0]/2, fftfreq[fftfreq > 0][-1]*2]
			XModel = np.logspace(np.log10(XRange[0]), np.log10(XRange[1]), 1000)
			YModel = Fourier.modelPink(XModel, PPink[0], PPink[1])
			YRange = [min(min(YModel),min(AmpSpec[fftfreq > 0])), max(max(YModel),max(AmpSpec[fftfreq > 0]))]
			p1 = Process(target=Graphing.plotMATPLOTLIB, args=[[fftfreq[fftfreq > Alpha_MinFreq],XModel],[AmpSpec[fftfreq > Alpha_MinFreq],YModel], [None,None],XRange,YRange,"log", YScale,LinesVert, [], "frequency, f [1/year]", "Amplitude, A", ["Data","Model"], ["black", "red"],["-", "--"],"cachefiles"+os.sep+"Fourier",Data_i_Name+NameDate,False])
			p1.start()
			p1.join()

		return FigAlpha, json.dumps(FourierStats)
	else:
		return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcFourierStatsEmpty())

#######################
# Summary Stats
#######################

@app.callback(
	Output('FourierTable', 'children'),
	[Input("FourierDataSummary","children"),Input("FourierFourierDataSummary","children")]
	)
def update_graph(Parameters, FourierStats):
	'''
    Load paramters into summary column

            Parameters:
                    Parameters (json): Parameters summarising Raw data
					FourierStats (json): Parameters summarising Fourier data

            Returns:
                    Dict (dict): Parameters summarising Raw data
    '''
	Parameters = json.loads(Parameters)
	FourierStats = json.loads(FourierStats)
	return build_fourierdatasummary(Parameters, FourierStats)

################################################################################################################
# Callbacks Tab 3:
################################################################################################################

#######################
# Dropdowns
#######################

@app.callback(
	[Output('AlphasColName-dropdown','options'),Output('AlphasColName-dropdown','value')],
	[Input('AlphasStrSearch', "value")],
	[State('RawDirect','children')],
	)
def update_dropdowns(StrSearch, RawDir):
	'''
    Update options for dropdown element for variables in Raw graphs

            Parameters:
                    StrSearch (float): Key substring to index files by
                    RawDir (float): Files directory

            Returns:
                    Dropdowns (options): List of possible dropdowns
					Value (value): Initial selected value
    '''
	global DefaultFeature
	DefaultFeature = StrSearch

	Files = DatM.GlobDirectory(RawDir)
	KeySelected = Misc.PatternsList(StrSearch, Files)
	if len(KeySelected) > 0:
		Value = KeySelected[0]
	else:
		KeySelected = Files
		Value = None
	
	return [{'label':"Variable: %s" % (name), 'value':name} for name in KeySelected], Value

#######################
# Load data
#######################

app.callback(
	Output('AlphasRawData', 'children'),
	[Input('RawDirect','children'), Input('AlphasColName-dropdown', 'value')]
)(LoadDataAfterDropdowns)

@app.callback(
	[Output('AlphasData', 'children'),Output("Spinner-tab3-B","children")],
	[Input('AlphasRun','n_clicks')],
	[State('AlphasRawData','children'), State('RawDirect','children'), State('AlphasDirect','children')])
def LoadAlphasData(n_clicks,jsonified_data, RawDir, AlphaDir):	
	'''
    Generate Alpha data

            Parameters:
                    n_clicks (int): A decimal integer
					jsonified_data (json): Jsonified data
                    RawDir (float): Files directory
					AlphaDir (float): Files directory

            Returns:
                    AlphaData (json): Jsonified data of alphas
					spinner (dcc.spinner): spinner object
    '''
	if jsonified_data not in [0,"0", None, "None"] and n_clicks not in [None]:
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		#Remove Timezone info that read_json puts in
		data.index = data.index.tz_localize(None) 
		Data_i_Name = data.columns[0]
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[Data_i_Name])
		units = Misc.CalcUnits(WindowParameters["Rate"],WindowParameters["RateUnit"])
		window = Misc.WindowSize(WindowParameters["Rate"], WindowParameters["RateUnit"], WindowUnit, WindowN)
	
		FileExists = DatM.CheckExists(RawDir, AlphaDir, Data_i_Name)
		if FileExists == True:
			Alphasdf = DatM.LoadData(AlphaDir, Data_i_Name)
		else:
			#Error estimated on mean devition beween points
			errs = Misc.errCalculation(data, WindowParameters["RateUnit"], True)	
			Alphasdf = Fourier.AlphasProgress(data[Data_i_Name].values, window, errs, units, Data_i_Name)
			Alphasdf.index = data.index
			writer = pd.ExcelWriter("%s%s%s.xlsx" % (AlphaDir, os.sep, Data_i_Name), mode="w")
			Alphasdf.to_excel(writer)
			writer.save()

		return Alphasdf.to_json(date_format='iso', orient='split'), ""

	else:
		return "0", ""


#######################
# RPlots
#######################

@app.callback(
	[Output('AlphasRawGraph', 'figure'),Output("AlphasDataSummary","children"),Output("AlphasProcess-Header", "children")],
	[Input('AlphasRawData','children'), Input('AlphasGraph', 'clickData'), Input("AlphasSigNum", "value")]
	)
def update_graph(jsonified_data, clickData, sig):
	'''
    Update Alpha Raw graph

            Parameters:
                    jsonified_data (json): Jsonified data
					clickData (dict): Click Data
					sig (float): Error scaling factor

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
					Header (str): Header above progress bar
                    
    '''
	if jsonified_data not in [0,"0", None, "None"]:
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		#Remove Timezone info that read_json puts in
		data.index = data.index.tz_localize(None) 
		Data_i_Name = data.columns[0]
		WindowParameters = CalcStats.CalcStats(data[Data_i_Name])

		f = Misc.timedeltaOneUnit(WindowN, WindowUnit)
		if clickData == None:		
			endval = data.index[-1]
			startval = endval - f
		elif clickData["points"][0]["pointIndex"] > len(data.index):
			endval = data.index[-1]
			startval = endval - f	
		else:
			endval = Misc.getDateTimeFromString(clickData["points"][0]["x"])
			startval = endval - f
			if endval > data.index[-1] or startval < data.index[0]:
				#CatchRefresh errors
				endval = data.index[-1]
				startval = endval - f

		
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[startval:endval][Data_i_Name])
		FigRaw = DashPlots.CreateRawFig(data, sig, Data_i_Name, WindowParameters, FigHeightPX/2)
		return FigRaw, json.dumps(WindowParameters), "Run all:"
	else:
		return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcStatsEmpty()), "Run all:"

@app.callback(
	[Output('AlphasGraph', 'figure'),Output("AlphasAlphasDataSummary","children")],
	[Input('AlphasData','children')],
	[State('AlphasRawData','children'), State('AlphasDirect','children'), State("AlphasSigNum","value")],
	)
def update_graph(jsonified_dataAlphas, jsonified_data, AlphaDir, sig):	
	'''
    Update Alpha Raw graph

            Parameters:
                    jsonified_dataAlphas (json): Jsonified Alpha data 
					jsonified_data (json): Jsonified data
					AlphaDir (str): Alpha data directory
					sig (float): Error scaling factor

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
                    
    '''
	if jsonified_data not in [0,"0", None, "None"] and jsonified_dataAlphas not in [0,"0", None, "None"]:
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		data.index = data.index.tz_localize(None)
		Data_i_Name = data.columns[0]
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[Data_i_Name])
		Alphasdf = pd.read_json(jsonified_dataAlphas, orient='split')
		Alphasdf.index = Alphasdf.index.tz_localize(None) 		
		Fig = DashPlots.CreateAlphasFig(Alphasdf, WindowParameters, sig, FigHeightPX/2, Data_i_Name)
	
		if SaveFigs == 1:
			XRange = [data.index[0],data.index[-1]]
			NameDate =  "_%s_%s" % (XRange[0].strftime("%d%m%Y"),XRange[1].strftime("%d%m%Y"))
			p1 = Process(target=Graphing.plotMATPLOTLIBAlpha, args=[data,Alphasdf,XRange,[None,None],"cachefiles"+os.sep+"Alpha",Data_i_Name+NameDate,True])
			p1.start()
			p1.join()

		return Fig, json.dumps(CalcStats.CalcAlphaStats(Alphasdf[Data_i_Name]))
	else:
		return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcAlphaStatsEmpty())

#######################
# Run all alphas
#######################

@app.callback(
	[Output("AlphasProcess-Button","children"),Output("Spinner-tab3-A", "children")],
	[Input('AlphasProcess-Button','n_clicks')],
	[State('AlphasProcess-Button','children') ,State('RawDirect','children'),State('AlphasDirect','children')],
	)
def update_graph(NClicks,ButtonState, RawDir, AlphaDir):
	'''
    Run all alpha anaylsis

            Parameters:
                    NClicks (dict): Clickdata 
					ButtonState (str): Button text
					RawDir (str): Raw data directory
					AlphaDir (str): Alpha data directory

            Returns:
					ButtonStr (str) : Button text 
					Spinner (dcc.spinner) : spinner object to display while loading
                    
    '''
	if NClicks not in [0, "0", None, "None"]:
		Files = DatM.GlobDirectory(RawDir)
		for Data_i_Name in Files:
			print(Data_i_Name)
			AlphaFileExists = DatM.CheckExists(RawDir, AlphaDir, Data_i_Name)
			if AlphaFileExists == True:
				continue
			else:
				data = DatM.LoadData(RawDir, Data_i_Name)
				# Statistics of interest
				WindowParameters = CalcStats.CalcStats(data[Data_i_Name])
				units = Misc.CalcUnits(WindowParameters["Rate"],WindowParameters["RateUnit"])
				window = Misc.WindowSize(WindowParameters["Rate"], WindowParameters["RateUnit"], WindowUnit, WindowN)
				#Error estimated on mean devition beween points
				errs = Misc.errCalculation(data, WindowParameters["RateUnit"], True)	
				Alphasdf = Fourier.AlphasProgress(data[Data_i_Name].values, window, errs, units, Data_i_Name)
				Alphasdf.index = data.index
				writer = pd.ExcelWriter("%s%s%s.xlsx" % (AlphaDir, os.sep, Data_i_Name), mode="w")
				Alphasdf.to_excel(writer)
				writer.save()
		return "Done", ""
	else:
		return ButtonState, ""

#######################
# Summary stats
#######################

@app.callback(
	Output('AlphasTable', 'children'),
	[Input("AlphasDataSummary","children"),Input("AlphasAlphasDataSummary","children")]
	)
def update_graph(Parameters, AlphaStats):
	'''
    Load paramters into summary column

            Parameters:
                    Parameters (json): Parameters summarising Raw data
					AlphaStats (json): Parameters summarising Alpha data

            Returns:
                    Dict (dict): Parameters summarising Raw data
    '''
	Parameters = json.loads(Parameters)
	AlphaStats = json.loads(AlphaStats)
	return build_Alphasdatasummary(Parameters, AlphaStats)

#######################
# Progress
#######################

@app.callback(
	[Output("AlphasProcess-Progress","children"), Output("AlphasProcess-Progress","value")],
	[Input("intervalMid","n_intervals")],
	[State('RawDirect','children'), State('AlphasDirect','children')]
	)
def update_graph(n_intervals, RawDir, AlphaDir):
	'''
    Progess bar updater

            Parameters:
                    n_interval (): Interval pulse
					RawDir (str): Raw data directory
					AlphaDir (str): Alpha data directory

            Returns:
					Percent (str): Percentage compleation
					value (float): Percentage compleation
                    
    '''
	Percentage =Misc.round_sig(DatM.CheckLog(RawDir,AlphaDir),2)
	return "%s" % (Percentage)+"\u0025"  , Percentage

################################################################################################################
# Callbacks Tab 4:
################################################################################################################

#######################
# Dropdowns
#######################

#Update options for dropdown element for variables in Raw graphs
@app.callback(
	[Output('BOCPDColName-dropdown','options'),Output('BOCPDColName-dropdown','value')],
	[Input('BOCPDStrSearch', "value")],
	[State('RawDirect','children')],
	)
def update_dropdowns(StrSearch, RawDir):
	'''
    Update options for dropdown element for variables in BOCPD graphs

            Parameters:
                    StrSearch (float): Key substring to index files by
                    RawDir (float): Files directory

            Returns:
                    Dropdowns (options): List of possible dropdowns
					Value (value): Initial selected value
    '''
	global DefaultFeature
	DefaultFeature = StrSearch

	Files = DatM.GlobDirectory(RawDir)
	KeySelected = Misc.PatternsList(StrSearch, Files)
	if len(KeySelected) > 0:
		Value = KeySelected[0]
	else:
		KeySelected = Files
		Value = None
	
	return [{'label':"Variable: %s" % (name), 'value':name} for name in KeySelected], Value

#######################
# Load data
#######################

#Update RawAlphas data
app.callback(
	Output('BOCPDRawData', 'children'),
	[Input('RawDirect','children'), Input('BOCPDColName-dropdown', 'value')]
)(LoadDataAfterDropdowns)

	
#Update BOCPD data
@app.callback(
	[Output('BOCPDData', 'children'), Output("Spinner-tab4-A","children")],
	[Input("BOCPDRun","n_clicks")],
	[State('BOCPDRawData','children'), State("BOCPDDirect", "children"), State("RawDirect", "children")], 
	)
def LoadAlphasData(n_clicks, jsonified_data, BOCPDDirectory, RawDir):
	'''
    Update BOCPD data

            Parameters:
					clickData (dict): Click Data
					jsonified_data (json): Jsonified data
					BOCPDDirectory (str): BOCPD Directory
					RawDirectory (str): Raw Directory

            Returns:
					JSON (json) : jsonified data
					spinner (dcc.spiner): Spinner object
                    
    '''
	if jsonified_data not in ["0", 0, None, "None"] and n_clicks not in [None]:
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		#Remove Timezone info that read_json puts in
		data.index = data.index.tz_localize(None) 
		Data_i_Name = data.columns[0]
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[Data_i_Name].dropna())
		units = Misc.CalcUnits(WindowParameters["Rate"],WindowParameters["RateUnit"])

		FileExists = DatM.CheckExists(RawDir, BOCPDDirectory, Data_i_Name)
		if FileExists == True:
			BOCPDdf = DatM.LoadData(BOCPDDirectory, Data_i_Name)
		else:
			#Error estimated on mean devition beween points
			errs = Misc.errCalculation(data, WindowParameters["RateUnit"], False)
			errs = np.sqrt(errs[1:]**2+errs[:-1]**2)			
			BOCPDdf, R_Max, Ps =  BOCPD.bocd(data[Data_i_Name].diff(1).values[1:], BOCPD_errsScale*errs)
			
			
			BOCPDdf = pd.DataFrame(BOCPDdf[:,:], index=data.index[1:])
			writer = pd.ExcelWriter("%s%s%s.xlsx" % (BOCPDDirectory, os.sep, Data_i_Name), mode="w")
			BOCPDdf.to_excel(writer)
			writer.save()

			Rmaxdf = pd.DataFrame(data={"R_Max":R_Max, "P":Ps}, index=data.index[1:])
			writer = pd.ExcelWriter("%s%s%s_R_Max.xlsx" % (BOCPDDirectory, os.sep, Data_i_Name), mode="w")
			Rmaxdf.to_excel(writer)
			writer.save()

		return BOCPDdf.to_json(date_format='iso', orient='split'), ""

	else:
		return "0",  ""


#######################
# Raw Plots
#######################

#Update Alpha graphs selected
@app.callback(
	[Output('BOCPDRawGraph', 'figure'), Output("BOCPDDataSummary","children")],
	[Input('BOCPDRawData','children'), Input('BOCPDGraph', 'clickData')],
	)
def update_graph(jsonified_data, clickData):
	'''
    Update BOCPD Raw graph

            Parameters:
					jsonified_data (json): Jsonified data
					clickData (dict): Clickdata

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
                    
    '''
	if jsonified_data not in ["0",0, None, "None"]:
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		#Remove Timezone info that read_json puts in
		data.index = data.index.tz_localize(None) 
		Data_i_Name = data.columns[0]
		
		#Click data
		WindowParameters = CalcStats.CalcStats(data[Data_i_Name].dropna())
		if clickData == None:		
			seqlen = 0
			endval = data.index[-1]
			startval = data.index[0]	
		else:
			seqlen = int(clickData["points"][0]["y"])
			endval = Misc.getDateTimeFromString(clickData["points"][0]["x"]) + Misc.timedeltaOneUnit(WindowParameters["Rate"],WindowParameters["RateUnit"])
			startval = endval - seqlen*Misc.timedeltaOneUnit(WindowParameters["Rate"],WindowParameters["RateUnit"])

		if startval < data.index[0] or endval > data.index[-1]:
			seqlen = 0
			endval = data.index[-1]
			startval = data.index[0]			

		WindowParameters = CalcStats.CalcStats(data[Data_i_Name][startval:endval].dropna())

		Fig = DashPlots.CreateRawFig(data, BOCPD_errsScale, Data_i_Name, WindowParameters, FigHeightPX/2)


		return Fig, json.dumps(WindowParameters)
	else:
		return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcStatsEmpty())

#Update Alpha graphs selected
@app.callback(
	[Output('BOCPDGraph', 'figure'),Output("BOCPDBOCPDDataSummary","children")],
	[Input('BOCPDData','children')],
	[State('BOCPDRawData','children')]
	)
def update_graph(jsonified_dataBOCPD,jsonified_data):
	'''
    Update BOCPD graph

            Parameters:
                    jsonified_dataAlphas (json): Jsonified Alpha data 
					jsonified_data (json): Jsonified data

            Returns:
					Fig (dcc.Graph) : Figure element 
					JSON (json) : jsonified summary data for display
                    
    '''
	if jsonified_dataBOCPD not in ["0",0, None, "None"] and jsonified_data not in ["0",0, None, "None"]:
		#Un json data
		data = pd.read_json(jsonified_data, orient='split')
		data.index = data.index.tz_localize(None) 
		Data_i_Name = data.columns[0]
		# Statistics of interest
		WindowParameters = CalcStats.CalcStats(data[Data_i_Name].dropna())
		WindowParameters["Start"] = Misc.unixTimeMillis(data.index[0])
		WindowParameters["End"] = Misc.unixTimeMillis(data.index[-1])
		BOCPDdf = pd.read_json(jsonified_dataBOCPD, orient='split')
		BOCPDdf.index = BOCPDdf.index.tz_localize(None) 
		R_Max = np.argmax(BOCPDdf.values,axis=1)
		Lines = BOCPDdf.index[np.argwhere(R_Max == 0).reshape(-1)]	
		if len(Lines) > 20:	
			Lines = []
			Fig = DashPlots.CreateBOCPDFig(BOCPDdf, R_Max, Lines, WindowParameters, BOCPD_tol,  FigHeightPX/2)
		else:
			Fig = DashPlots.CreateBOCPDFig(BOCPDdf, R_Max, Lines, WindowParameters, BOCPD_tol,  FigHeightPX/2)

		Stats = CalcStats.CalcBOCPDStats(R_Max, BOCPD_tol)

		if SaveFigs == 1:
			Name = Data_i_Name
			NameDate =  "_%s_%s" % (BOCPDdf.index[0].strftime("%d%m%Y"),BOCPDdf.index[-1].strftime("%d%m%Y"))
			p1 = Process(target=Graphing.plotMATPLOTLIBBOCPDHeat, args=[BOCPDdf.index, data[Data_i_Name].dropna().values[1:],data["Error"].dropna().values[1:], R_Max, BOCPDdf.values, BOCPD_tol,  Misc.timedeltaOneUnit(WindowParameters["Rate"],WindowParameters["RateUnit"]), [BOCPDdf.index[0],BOCPDdf.index[-1]], [0,int(max(R_Max)*1.2)], Lines, "Time, t", Data_i_Name, "cachefiles"+os.sep+"BOCPD", Name+NameDate, True])
			p1.start()
			p1.join()

		return Fig, json.dumps(Stats)
	else:
		return DashPlots.EmptyFig(FigHeightPX/2), json.dumps(CalcStats.CalcBOCPDStatsEmpty())

#######################
# Summary stats
#######################

@app.callback(
	Output('BOCPDTable', 'children'),
	[Input("BOCPDDataSummary","children"),Input("BOCPDBOCPDDataSummary","children")]
	)
def update_graph(Parameters, BOCPDStats):
	'''
    Load paramters into summary column

            Parameters:
                    Parameters (json): Parameters summarising Raw data
					BOCPDStats (json): Parameters summarising BOCPD data

            Returns:
                    Dict (dict): Parameters summarising Raw data
    '''
	Parameters = json.loads(Parameters)
	BOCPDStats = json.loads(BOCPDStats)
	return build_BOCPDdatasummary(Parameters, BOCPDStats)


#######################
# Progress
#######################

#Callback to update processbar
@app.callback(
	[Output("BOCPDProcess-Progress","children"), Output("BOCPDProcess-Progress","value")],
	[Input("intervalMid","n_intervals")],
	[State("RawDirect", "children"),State('BOCPDDirect','children')]
	)
def update_graph(n_intervals, RawDir, BOCPDDirectory):
	'''
    Progess bar updater

            Parameters:
                    n_interval (): Interval pulse
					RawDir (str): Raw data directory
					BOCPDDir (str): Alpha data directory

            Returns:
					Percent (str): Percentage compleation
					value (float): Percentage compleation
                    
    '''
	Percentage =Misc.round_sig(DatM.CheckLog(RawDir,BOCPDDirectory),2)
	return "%s" % (Percentage)+"\u0025"  , Percentage

#######################
# Run all BOCPD
#######################

#Run all when button pushed.
@app.callback(
	[Output("BOCPDProcess-Button","children"),Output("Spinner-tab4-B", "children")],
	[Input('BOCPDProcess-Button','n_clicks')],
	[State('BOCPDProcess-Button','children'), State('RawDirect','children'), State('BOCPDDirect','children')],
	) 
def update_graph(NClicks, ButtonState, RawDir, BOCPDDirectory):
	'''
    Run all BOCPD anaylsis

            Parameters:
                    NClicks (dict): Clickdata 
					ButtonState (str): Button text
					RawDir (str): Raw data directory
					BOCPDDir (str): BOCPD data directory

            Returns:
					ButtonStr (str) : Button text 
					Spinner (dcc.spinner) : spinner object to display while loading
                    
    '''
	if NClicks not in [0, "0", None, "None"]:
		Files = DatM.GlobDirectory(RawDir)
		for Data_i_Name in Files:
			FileExists = DatM.CheckExists(RawDir, BOCPDDirectory, Data_i_Name)
			if FileExists == True:
				continue
			else:
					#Run Anaylsis
					data = DatM.LoadData(RawDir, Data_i_Name)
					WindowParameters = CalcStats.CalcStats(data)
					
					#Error estimated on mean devition beween points
					errs = Misc.errCalculation(data, WindowParameters["RateUnit"], False)
					errs = np.sqrt(errs[1:]**2+errs[:-1]**2)		
					BOCPDdf, R_Max, Ps =  BOCPD.bocd(data[Data_i_Name].diff(1).values[1:], BOCPD_errsScale*errs)

					BOCPDdf = pd.DataFrame(BOCPDdf[:,:], index=data.index[1:])
					writer = pd.ExcelWriter("%s%s%s.xlsx" % (BOCPDDirectory, os.sep, Data_i_Name), mode="w")
					BOCPDdf.to_excel(writer)
					writer.save()

					Rmaxdf = pd.DataFrame(data={"R_Max":R_Max, "P":Ps}, index=data.index[1:])
					writer = pd.ExcelWriter("%s%s%s_R_Max.xlsx" % (BOCPDDirectory, os.sep, Data_i_Name), mode="w")
					Rmaxdf.to_excel(writer)
					writer.save()
		return "Done", ""
	else:
		return ButtonState, ""

################################################################################################################
# Callbacks Tab 5:
################################################################################################################

#######################
# Dropdowns
#######################

#Update options for dropdown element for variables in PCA graphs
@app.callback(
	[Output('PCAColName-dropdown','options'),Output('PCAColName-dropdown','value')],
	[Input('PCAStrSearch', "value"),Input('PCATypeSelect','value')],
	)
def update_dropdowns(StrSearch, Type):
	'''
    Update options for dropdown element for variables in PCA graphs

            Parameters:
                    StrSearch (float): Key substring to index files by
                    RawDir (float): Files directory

            Returns:
                    Dropdowns (options): List of possible dropdowns
					Value (value): Initial selected value
    '''
	if Type == "Alpha":
		Dir = "data"+os.sep+"AlphaData"
	if Type == "Raw":
		Dir = "data"+os.sep+"RawData"
	if Type == "BOCPD":
		Dir = "data"+os.sep+"BOCPDData"
	Files = DatM.GlobDirectory(Dir)
	KeySelected = Misc.PatternsList(StrSearch, Files)

	if Type == "BOCPD":
		KeySelected = Misc.PatternsList("R_Max", KeySelected)

	global DefaultFeature
	DefaultFeature = StrSearch

	global DefaultDataType
	DefaultDataType = Type
	return [{'label':"Variable: %s" % (name), 'value':name} for name in Files], KeySelected

@app.callback(
	[Output('PCATestFeature-dropdown','options'), Output('PCATestFeature-dropdown','value')],
	[Input('PCAStrSearch', "value"),Input('PCATypeSelect','value')],
	)
def update(StrSearch, Type):
	'''
    Marginal dropdown

            Parameters:
                    StrSearch (str): Search string
                    Type (str): "Alpha" "Raw" "BOCPD"

           Returns:
                    Dropdowns (options): List of possible dropdowns
					Value (value): Initial selected value
    '''
	if Type == "Alpha":
		Dir = "data"+os.sep+"AlphaData"
	if Type == "Raw":
		Dir = "data"+os.sep+"RawData"
	if Type == "BOCPD":
		Dir = "data"+os.sep+"BOCPDData"
	Files = DatM.GlobDirectory(Dir)
	KeySelected = Misc.PatternsList(StrSearch, Files)
	if Type == "BOCPD":
		KeySelected = Misc.PatternsList("R_Max", KeySelected)
	return [{'label':"Variable: %s" % (name), 'value':name} for name in KeySelected], None 

#######################
# RunPCA
#######################

@app.callback(
	[Output('PCARun','children'), Output("PCAData","children"), Output("PCATsData","children"), Output("PCAQsData","children"), Output("DataSummary","children"), Output("PCADataSummary","children"), Output("Spinner-tab5-A", "children")],
	[Input('PCARun','n_clicks')],
	[State('PCATypeSelect','value'), State('PCAColName-dropdown','value'), State('PCAStrSearch', "value")]
	)
def update_graph(nclicks, Type, Vars, StringSearch):
	'''
    Run PCA anaylsis

            Parameters:
                    nclick (int): Number of times button has been clicked
                    Type (str): "Alpha" "Raw" "BOCPD"
					Vars (list): List of features
					StrSearch (str): Search string

            Returns:
                    PCARun (str): Button text
					PCAData (json): jsonified PCA data
					PCATsData (json): jsonified Ts data
					PCAQsData (json): jsonified Q data
					Dict (dict): Parameters summarising Raw data
					Dict (dict): Parameters summarising PCA data
					spinner (dcc.spinner): spinner object for when loading
    '''
	if Type == "Alpha":
		Dir = "data"+os.sep+"AlphaData"
	if Type == "Raw":
		Dir = "data"+os.sep+"RawData"
	if Type == "BOCPD":
		Dir = "data"+os.sep+"BOCPDData"
	if nclicks in [None]:
		return "Run", "", "", "", json.dumps(CalcStats.CalcStatsEmpty()), json.dumps(CalcStats.CalcPCAStatsEmpty()), ""
			
	PCA_NPCA, PCA_AlphaLim, _ =  Misc.GetOptimzed(PCA_FittedParams, Type, StringSearch, DefaultMetric, Vars)

	#Get crashing cases out of the way
	if Vars in  [None,"None"]: #More Features not selected
		return "Run", "", "", "", json.dumps(CalcStats.CalcStatsEmpty()), json.dumps(CalcStats.CalcPCAStatsEmpty()), ""
	elif PCA_NPCA > len(Vars): #More PCA components than dimensions
		return "Run", "", "", "", json.dumps(CalcStats.CalcStatsEmpty()), json.dumps(CalcStats.CalcPCAStatsEmpty()), ""
	else:
		TestCol = Vars[0]
		#Load Datas into one large DF
		df, _ = DatM.PCALOAD(Dir,Vars)
		if df.empty: #Checks to make sure senible to plot
			return "Run", "", "", "", json.dumps(CalcStats.CalcStatsEmpty()), json.dumps(CalcStats.CalcPCAStatsEmpty()), ""
			
		WindowParameters = CalcStats.CalcStats(df.iloc[:,0])
		window = Misc.WindowSize(WindowParameters["Rate"], WindowParameters["RateUnit"], PCA_WindowUnit, PCA_WindowN)
		dtMeasure = Misc.timedeltaOneUnit(WindowParameters["Rate"], WindowParameters["RateUnit"])

		if df.shape[0] < window:
			return "Run", "", "", "", json.dumps(CalcStats.CalcStatsEmpty()), json.dumps(CalcStats.CalcPCAStatsEmpty()), ""
			
		DataPCA, Ts, Qs, Variances = PCA.PCA(df, PCA_NPCA, window) 
		RegionsAll, _, _, _ =  PCA.PCARegionsCollect(Ts, Qs, dtMeasure, PCA_AlphaLim, PCA_NPCA, TestCol)
		#Just care about time periods
		PCAStats = CalcStats.CalcPCAStats(Ts, Qs, PCA_NPCA, Variances, RegionsAll)

		
		return "Run", DataPCA.to_json(date_format='iso', orient='split'), Ts.to_json(date_format='iso', orient='split'), Qs.to_json(date_format='iso', orient='split'), json.dumps(WindowParameters), json.dumps(PCAStats), ""

#######################
# Graphing
#######################

@app.callback(
	[Output('PCAGraph', 'figure') ,Output('RatesGraph', 'figure')],
	[Input("PCATestFeature-dropdown", "value"),Input("PCAData","children"), Input("PCATsData","children"), Input("PCAQsData","children")],
	[State("DataSummary","children"),State('PCATypeSelect','value'), State('PCAStrSearch', "value")]
	)
def update_graph(MarginalFeature, DataPCA, Ts, Qs, WindowParameters, Type, StringSearch):
	'''
    Plot PCA graphs

            Parameters:
					MarginalFeature (str): Feature to plot marginalised
                    DataPCA (json): jsonified PCA data
					Ts (json): jsonified Ts data
					Qs: (json): jsonified Q data
					WindowParameters (json): summary of raw data
					Type (str): "Alpha" "Raw" "BOCPD"
					StrSearch (str): Search string

            Returns:
					PCAGraph (dcc.graph): Graph of PCA features
					RatesGraph (dcc.graph): Graph of rolling rates
    '''
	if Ts in [None, "", "0", 0] or Qs in [None, "", "0", 0]:
		return DashPlots.EmptyFig(FigHeightPX/3),DashPlots.EmptyFig(2*FigHeightPX/3)
	else:
		DataPCA = pd.read_json(DataPCA, orient='split')
		Ts = pd.read_json(Ts, orient='split')
		Qs = pd.read_json(Qs, orient='split')		
		
		WindowParameters = json.loads(WindowParameters)
		if MarginalFeature not in DataPCA.columns:
			TestCol = DataPCA.columns[0]
		else:
			TestCol = MarginalFeature

		PCA_NPCA, PCA_AlphaLim, PCA_Thresh =  Misc.GetOptimzed(PCA_FittedParams, Type, StringSearch, DefaultMetric, DataPCA.columns)
	
		NDur = 0
		if Type == "BOCPD":
			NDur = -1
		dtMeasure = Misc.timedeltaOneUnit(WindowParameters["Rate"], WindowParameters["RateUnit"])
		RegionsAll, RegionsSpecific, RatesAll, RatesSpecific =  PCA.PCARegionsCollect(Ts, Qs, dtMeasure, PCA_AlphaLim, PCA_NPCA, TestCol, NDur)
		
		
		if MarginalFeature not in [None]:
			FigPCA =  DashPlots.CreatePCADataFig(DataPCA, RegionsAll, RegionsSpecific, MarginalFeature, NDur, int(FigHeightPX/3)) 
			FigRates = DashPlots.CreateRatesFig("Rate", PCA_Thresh, RatesAll, RatesSpecific,  RegionsAll, RegionsSpecific, MarginalFeature, NDur, int(2*FigHeightPX/3))
		else:
			FigPCA =  DashPlots.CreatePCADataFig(DataPCA, RegionsAll, 0, MarginalFeature, NDur, int(FigHeightPX/3)) 
			FigRates = DashPlots.CreateRatesFig("Rate", PCA_Thresh, RatesAll, RatesSpecific, RegionsAll, 0, MarginalFeature, NDur, int(2*FigHeightPX/3))

		if SaveFigs == 1 and len(DataPCA.columns) < 6:
			Name = ""
			for V in DataPCA.columns:
				Name +=V
			XRange = [DataPCA.index[0],DataPCA.index[-1]]
			NameDate =  "_%s_%s" % (XRange[0].strftime("%d%m%Y"), XRange[-1].strftime("%d%m%Y"))
			p1 = Process(target=Graphing.plotMATPLOTLIBPCA, args=[DataPCA, Ts, Qs, XRange, [1e-16,2], [PCA_AlphaLim], RegionsAll, RegionsSpecific, "cachefiles"+os.sep+"PCA", Name+NameDate, True])
			p1.start()
			p1.join()
	return FigPCA, FigRates

#######################
# Summary stats
#######################

@app.callback(
	Output('PCATable', 'children'),
	[Input("DataSummary","children"),Input("PCADataSummary","children")]
	)
def update_graph(Parameters, PCAStats):
	'''
    Load paramters into summary column

            Parameters:
                    Parameters (json): Parameters summarising Raw data
					PCAStats (json): Parameters summarising PCA data

            Returns:
                    Dict (dict): Parameters summarising Raw data
    '''
	Parameters = json.loads(Parameters)
	PCAStats = json.loads(PCAStats)
	return build_PCAdatasummary(Parameters, PCAStats)

#######################
# Cache
#######################

@app.callback(
	Output("JSON_Cache_Output", "children"),
	[Input("PCADataSummary","children")],
	[State("DataSummary","children"), State('PCARun','n_clicks'), State('PCATypeSelect','value'), State('PCAColName-dropdown','value'), State("PCATsData","children"), State("PCAQsData","children"), State('PCAStrSearch', "value")],
	)
def update_graph(PCAStats, WinPara, n_clicks, Type, Vars, Ts, Qs, StringSearch):
	'''
    Plot PCA graphs

            Parameters:
					PCAStats (json): summary of PCA data
					WinPara (json): summary of raw data
					n_clicks (int): Number of clicks on run button
					Type (str): "Alpha" "Raw" "BOCPD"
					Vars (list): List of features
					Ts (json): jsonified Ts data
					Qs: (json): jsonified Q data
					StrSearch (str): Search string

            Returns:
					A (int): 0
    '''
	if SaveCache == 0:
		return 0
	if Ts in [None, 0, "0", "None", ""]:
		return 0
	if n_clicks not in [None] or Vars not in [None]:
		if len(Vars) == 0:
			return 0
		PCAStats = json.loads(PCAStats)
		WinPara = json.loads(WinPara)
		Ts = pd.read_json(Ts, orient='split')
		Qs = pd.read_json(Qs, orient='split')

		PCA_NPCA, PCA_AlphaLim, PCA_Thresh =  Misc.GetOptimzed(PCA_FittedParams, Type, StringSearch, DefaultMetric, Vars)	

		dtMeasure = Misc.timedeltaOneUnit(WinPara["Rate"], WinPara["RateUnit"])
		RegionsAll, _, _, _ =  PCA.PCARegionsCollect(Ts, Qs, dtMeasure, PCA_AlphaLim, PCA_NPCA, 0)
		
		STARTS = []
		ENDS = []
		DURATIONS = []
		for Ri in range(RegionsAll.shape[0]):
			STARTS.append(Misc.unixToDatetime(RegionsAll.iloc[Ri]["Starts"]).strftime('%d/%m/%Y %H:%M:%S'))
			ENDS.append(Misc.unixToDatetime(RegionsAll.iloc[Ri]["Stops"]).strftime('%d/%m/%Y %H:%M:%S'))
			DURATIONS.append("%s" % RegionsAll.iloc[Ri]["Duration"])

		Name = "PCA"
		FileName = "cachefiles"+os.sep+"%s.json" % (Name)
		data_i = {}

		WinPara["Start"] = "%s" % Misc.unixToDatetime(WinPara["Start"]).strftime('%d/%m/%Y %H:%M:%S')
		WinPara["End"] = "%s" % Misc.unixToDatetime(WinPara["End"]).strftime('%d/%m/%Y %H:%M:%S')

		data_i["Time"] = "%s" % datetime.now().strftime('%d/%m/%Y %H:%M:%S')
		data_i["Type"]  = Type
		data_i["Features"]  = Vars
		data_i["Stats"] = WinPara
		data_i["PCAStats"] = PCAStats
		data_i["Regions"] = []
		data_i["Regions"].append({"Starts" : STARTS})
		data_i["Regions"].append({"End" : ENDS})
		data_i["Regions"].append({"Duration" : DURATIONS})
		DatM.WriteCacheFile(FileName, data_i)
	return 0
	
#######################
# Reset Folders data
#######################

def EmptyFolders():
	'''
    Delete local data and cache files

            Parameters:

            Returns:
					A (int): Return if completed
    '''
	import glob
	files = glob.glob('data'+os.sep+'*'+os.sep+'*.xlsx')
	files += glob.glob('cachefiles'+os.sep+'*'+os.sep+'*.png')
	files += glob.glob('cachefiles'+os.sep+'*.json')
	for F in files:
		print("Deleting %s" % F)
		os.remove(F)
	return 1

#######################
# argv
#######################

def main(argv):
	'''
    Python run parameters

            Parameters:
					argv (list): Python terminal input args

            Returns:
					Delete (bool): T/F Reset folders data 
    '''
	#Defualt parameters
	Delete=False
	try:
		opts, args = getopt.getopt(argv,"D",["Delete="])
	except getopt.GetoptError:
		print('python app.py -D')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('python app.py -D')
			sys.exit()
		elif opt in ("-D"):
			Delete = True
	return Delete
	
if __name__ == "__main__":
	Delete = main(sys.argv[1:])
	if Delete:
		EmptyFolders()
	print("Run app dashboard")
	app.config.suppress_callback_exceptions = True	
	#Run as debug mode
	app.run_server(debug=True, port=8050, threaded= True)
	#Run normally
	#app.run_server(host= "0.0.0.0", port=8050, threaded= True)
