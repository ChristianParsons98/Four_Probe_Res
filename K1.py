#This Python file interfaces with a Keithley2400 Sourcemeter. The algorithm measures the resistance
# using the 4 probe method. It measures one with current in the positive direction, then measures
# with current in the negative direction. The plot will show the average of these two measurements vs. temp.
#Author: Christian Parsons
#First Created: 13 July 2022
#Last Updated: 28 June 2024

import pyvisa
import time
import csv
import win32api
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

#The instruments need to be turned on before they will show up here.
#Opening a Resource Manager - Uses Labview backend, NI, to interface with Instruments.
rm = pyvisa.ResourceManager()

#Printing the attached interfacable instruments. ASLR1 and 3 are the keyboard and mouse.
#print(rm.list_resources())

#Define the instrument as an object in python.

#This is the thermometer
Therm=rm.open_resource("GPIB0::12::INSTR")

#This is the Keithley2400 SourceMeter
keithley2400=rm.open_resource("GPIB0::24::INSTR")

#This function Measures the 4 probe resistance with current flowing in both the positive and negative direction.
#Manually set the current range for the measurement.
#Gives the results as a list of floats [Resistance_Positive,Current_Positive,Resistance_Flipped,Current_Flipped]
#Units are Ohm and Amp.
def RFlipManual(InCur):
    #Reset the instrument settings to default - so we know what we are starting with
    keithley2400.write("*rst; status:preset; *cls")

    #Switch the instrument into Resistance measurement mode.
    keithley2400.write('Func "RES"')

    #Set to Manual mode for applied current
    keithley2400.write('RES:MODE MAN')
   
    #InCur set to False if the user wants to use AutoCurrent Mode
    if not InCur:
        #Set the K2400 to Auto Ohms Mode - Let the K2400 figure out the ideal source current.
        keithley2400.write('RES:MODE Auto')
    #Otherwise we are in manual current set mode.
    else:
        #Setting the forward current based on user input
        CurrCmd1= ':SOUR:CURR:LEV '+InCur
        keithley2400.write(CurrCmd1)

    #Switch into 4 wire sensing mode
    keithley2400.write(':SYST:RSEN ON')

    #Wait a thenth of a second before measureing the resistance.
    time.sleep(0.1)

    #Tell K2400 We are reading out the Resistance
    keithley2400.write(':FORM:ELEM RES')

    #Turning on the current
    keithley2400.write(':OUTP ON')

    #Get the resistance Reading
    Res1 = keithley2400.query(':READ?')
   
    #Ask K2400 what the current is from the AUTO mode.
    Curr1= keithley2400.query(':SOUR:CURR:LEV?')

    #Switch to Manual mode to flip the current direction
    keithley2400.write('RES:MODE MAN')

    #Flipping the current from the first measurement
    CurrCmd= ':SOUR:CURR:LEV -'+Curr1
    keithley2400.write(CurrCmd)
   
    #Ask K2400 what the current is to double check that it is correct
    Curr2 = keithley2400.query(':SOUR:CURR:LEV?')

    #Again, wait a tenth of a second before measuring the resistance.
    time.sleep(0.1)

    #Get the resistance Reading
    Res2 = keithley2400.query(':READ?')

    #Turn off the current
    keithley2400.write(':OUTP OFF')
   
    #Return the results
    return [float(Res1),float(Curr1),float(Res2),float(Curr2)]

#This takes care of all user interaction inclusing instructions and user input.
def UserInteractionM():
    #Instructions
    print("User Guide:")
    print("To stop data colelction: Hold Q and Space until program ends.")
    print("To display a plot: Hold P and Space until plot is displayed.")
    print("File Naming: You must include the .csv after your file name in the next step.")
    #User Input
    print("User Input:")
    filename = input("Enter Datafile Name in the form name.csv: ")
    UserTime= input("Set wait time between measurements in seconds: ")
    mode = input("Type A for AutoCurrent mode, or M to Manually set Current: ")
    if mode=='M':
        SetCur = input("Set the applied current in Amps (ex: 0.01): ")
        return [filename,UserTime,SetCur]
    else:
        return [filename,UserTime,False]

#Creates a csv file with the user entered name and writes the header to to file.
#File is closed at the end.
def InitializeFile(csv_file_name):
    f = open(csv_file_name,"x",newline="")
    myheader=['Temperature(K)','Average Resistance(Ohms)','R_ForwardI(Ohms)','ForwardI(Amps)','R_Backward(Ohms)',
              'BackwardI(Amps)','Time_Since_Start(s)','True_Time(s)']
    writer=csv.writer(f)
    writer.writerow(myheader)
    f.close()

#Defining a function which allows me to write a measurement ('fullMeasurement') to an already initialized csv file.
def WriteMeasurement(csv_file_name,fullMeasurement):
    #Open the file which becomes an object f.
    f = open(csv_file_name,"a",newline="")
    #Define an object that can write to object f (csv file).
    writer=csv.writer(f)
    #Write the measurement as a row
    writer.writerow(fullMeasurement)
    #Close the file.
    f.close()
   
def PlotData(csv_file_name):
    #Open the csv as a pandas dataframe
    df=pd.read_csv(csv_file_name)
    #Pull the avg R and Temp data as numpy arrays
    R=np.asarray(df['Average Resistance(Ohms)'])
    Temp=np.asarray(df['Temperature(K)'])
   
    #Generate the figure
    plt.plot(Temp,R)
    plt.title('Sample Avg Resistance vs. Temp')
    plt.xlabel('Temperature (K)')
    plt.ylabel('Avergave Resistance (Ohm)')
    filename=csv_file_name[:-4]+'.png'
    plt.savefig(filename,dpi=300)
    print('plt saved at '+filename)
   
   

#Defining the function to take measurements and write to a csv file.
#This will run until you hold q and space just before a measurement.
#The function requires you to give it True if you want to manually set the current, False for autoset current.
#In reality the algorithm will take a measurement every ~WaitT+0.4s so adjust accordingly if needed.

def ResistivityFlipM():
    #Get info from use. SetCur=False if the user chose AutoCurrent Mode
    csv_file_name,UserTime,SetCur = UserInteractionM()
   
    #Initialize the file that the data will be written to. This will throw an error if the file already exists.
    InitializeFile(csv_file_name)
   
    #Setup the end condition. Initially the user has not yet pressed Q and Space. ie we are not at the end condition.
    NoQ=True
    #Get the start time of the experiment. Will be used to give time relative to the start of the measurement.
    timestart=time.time()
   
    #Run until the end condition is met
    while NoQ:
        #Taking the Measurement
       
        #Figure out how much time has passed since the start of the measurement.
        TimeN=time.time()
        TimeDiff=TimeN-timestart
       
        #Try except allows the program to continue running even if errors start occuring.
        try:
            RRaw = RFlipManual(SetCur)
           
        except:
            print('Warning! Error occured when measuring the Resistance.')
            #When an error occurs, set everything to 0.
            RRaw = [0,0,0,0]
       
        #Get the Temperature measurement in K
        Temp= np.double(Therm.query(":READ?"))
       
        #Take the average of the forward and reverse measurements.
        Ravg=((RRaw[0]+RRaw[2])/2.)
       
        #Figure out how much time has passed since the start of the measurement.
        Timenow=time.time()
        TimeDiff=Timenow-timestart
       
        #This is the full set of info to write to the output file.
        fullMeasurement=[Temp,Ravg,*RRaw,TimeDiff,Timenow]
       
        #Write the full measurement as a row to the user given file name.
        WriteMeasurement(csv_file_name,fullMeasurement)
       
        Tnow=time.time()
        TDiff=Tnow-TimeN
        while float(TDiff)<float(UserTime) and NoQ==True:
       
            #If the User is pressing both Q (0x51) and Space (0x20)
            if win32api.GetKeyState(0x51)<0 and win32api.GetKeyState(0x20)<0:
                NoQ=False
            #If the User is pressing both P (0x50) and Space (0x20)
            if win32api.GetKeyState(0x50)<0 and win32api.GetKeyState(0x20)<0:
                PlotData(csv_file_name)
            #Otherwise do nothing
            else:
                pass
            #Wait to take the next measurement.
            time.sleep(0.02)
           
            #Update the time difference
            Tnow=time.time()
            TDiff=Tnow-TimeN

#Run the code
ResistivityFlipM()
