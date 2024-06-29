#This Python file interfaces with a Keithley2400 Sourcemeter and Keithley2182 NanoVoltMeter.
# The algorithm measures the resistance using the 4 probe method. It measures one with current in the positive direction,
# then measures with current in the negative direction. The plot will show the average of these two measurements vs. temp.
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

#Define the instrument as an object in python.

#This is the thermometer
Therm=rm.open_resource("GPIB0::12::INSTR")

#This is the Keithley2400 SourceMeter
keithley2400=rm.open_resource("GPIB0::24::INSTR")

#This is the Keithley 2182 NanoVoltMEter
KNVM=rm.open_resource("GPIB0::7::INSTR")

#This function initializes the instruments for the appropriate measurements.
def Ins_Initialize():
    #Reset the instrument settings to default - so we know what we are starting with
    keithley2400.write("*rst; status:preset; *cls")
    KNVM.write("*rst; status:preset; *cls")
   
    #Set the 2400 into Source Current mode with a fixed current output.
    keithley2400.write('SOUR:FUNC CURR')
    keithley2400.write('SOUR:CURR:MODE FIXED')
   
    #Set the 2182 to measure voltage off of channel 1.
    KNVM.write(":SENS:CHAN 1")
    KNVM.write(":SENS:FUNC 'VOLT'")

   
#This function will measure voltage across the sample with current in both the positive and negative direction.
#Takes Current as a float in Amps - For example 0.00001
#Takes delay time in seconds - For example 1.0
#Returns a list [VoltP,CurrP,ResP,TempP,VoltN,CurrN,ResN,TempN]
def Measure_R(Current,delay):
    #Setting the Source Current Manually
    CurrCmd= ':SOUR:CURR:LEV '+str(Current)
    keithley2400.write(CurrCmd)
    #Turning on the current
    keithley2400.write(':OUTP ON')
    #Ask K2400 what the current is. This is a check that it was properly set.
    CurrP= float(keithley2400.query(':SOUR:CURR:LEV?'))
    #Get the resistance reading for positive current.
    VoltP = float(KNVM.query(':READ?'))
    #Turn off the current after measuring voltage.
    keithley2400.write(':OUTP OFF')
    #Read the temperature
    TempP=float(Therm.query(":READ?"))
    #Delay between Plus and Negative current measurements.
    time.sleep(delay)
   
   
    #Now do the same thing but with negative current.
    CurrCmd= ':SOUR:CURR:LEV -'+str(Current)
    keithley2400.write(CurrCmd)
    #Turning on the current
    keithley2400.write(':OUTP ON')
    #Ask K2400 what the current is. This is a check that it was properly set.
    CurrN= float(keithley2400.query(':SOUR:CURR:LEV?'))
    #Get the resistance reading for Negative current.
    VoltN = float(KNVM.query(':READ?'))
    #Turn off the current after measuring voltage.
    keithley2400.write(':OUTP OFF')
    #Read the temperature. More relevant if delay time is long.
    TempN=float(Therm.query(":READ?"))

   
    #Calculate Resistance
    ResP=VoltP/CurrP
    ResN=VoltN/CurrN
    Res_Avg=(ResP+ResN)/2.
   
    return [TempP,Res_Avg,VoltP,CurrP,ResP,TempN,VoltN,CurrN,ResN]
   

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
    UserTime= input("Set wait time (2 or greater) between measurements in seconds: ")
    print("Do not set a current above 0.01 unless you know what you are doing.")
    SetCur = input("Set the applied current in Amps (ex: 0.00001): ")
    return [filename,UserTime,SetCur]


#Creates a csv file with the user entered name and writes the header to to file.
#File is closed at the end.
#[TempP,Res_Avg,VoltP,CurrP,ResP,TempN,VoltN,CurrN,ResN]
def InitializeFile(csv_file_name):
    f = open(csv_file_name,"x",newline="")
    myheader=['Temperature_Forward(K)','Average_Resistance(Ohms)','V_Forward(V)','ForwardI(Amps)','R_ForwardI(Ohms)',
              'Temperature_Backward(K)','V_Backward(V)','BackwardI(Amps)','R_Backward(Ohms)',
              'Time_Since_Start(s)','True_Time(s)']
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
    R=np.asarray(df['Average_Resistance(Ohms)'])
    Temp=np.asarray(df['Temperature_Forward(K)'])
   
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
            RRaw = Measure_R(SetCur,1.0)
           
        except:
            print('Warning! Error occured when measuring the Resistance.')
            #When an error occurs, set everything to 0.
            RRaw = [0.,0.,0.,0.,0.,0.,0.,0.,0.]
       
        #Figure out how much time has passed since the start of the measurement.
        Timenow=time.time()
        TimeDiff=Timenow-timestart
       
        #This is the full set of info to write to the output file.
        fullMeasurement=[*RRaw,TimeDiff,Timenow]
       
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
