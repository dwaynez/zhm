#!/usr/bin/python
license=""" 
Copyright (C) Dwayne Zon 2015 <dwayne.zon@gmail.com> 

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation
""" 
version_long='V1.0: <2015-01-09>'
program_name='zhmservice'
version_short='V1.0'

import datetime
import sqlite3
import threading, queue
from multiprocessing import Process
from multiprocessing.connection import Client
import getopt
import sys
import zhmutils # zhm db interface
import time
import glob
import os
import RPi.GPIO as GPIO
import zhmalarm
import subprocess
import locale
import socket
from multiprocessing.connection import Listener

# Thread to monitor communication from other devices (just Android for now)
class monitor_comm(threading.Thread):
    global garagebutton
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.stoprequest = threading.Event()
        
    def run(self):
        global garagebutton
        address = ('0.0.0.0', 6002) 
        ##address = ('192.168.39.18', 6004) 
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(address)
        sock.listen(10)
        while not self.stoprequest.isSet():
            try:
                #~ print("Waiting for a connection")
                (clientsocket, address) = sock.accept()
                clientsocket.settimeout(1)
                try:
                    msg = clientsocket.recv(16)
                    if msg == b"GarageButton\n":
                        print("Requesting Garage Button")
                        lock.acquire()
                        garagebutton = True
                        lock.release()
                except:
                    clientsocket.close()
            except:
                time.sleep(1)
        sock.close()
    
    # If client says time to shutdown, tell the thread
    def join(self, timeout=None):
        print("Monitor comm thread join called")  
        self.stoprequest.set()
        super(monitor_comm, self).join(timeout)
        print("Monitor comm thread told to shutdown")  

# Thread to monitor the Spartan alarm system
class monitor_alarm_system(threading.Thread): 
    global alarmcode_q
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.stoprequest = threading.Event()

    def run(self):
        zhmalarm.monitoralarm(self.processalarmcode)
        while not self.stoprequest.isSet():
            time.sleep(1)
        print("alarm thread is ending")

    def processalarmcode(self,code):
        #~ print("Process alarm code=",code)
        alarmcode_q.put(code)

    # If client says time to shutdown, tell the thread
    def join(self, timeout=None):
        zhmalarm.cleanup()
        self.stoprequest.set()
        super(monitor_alarm_system, self).join(timeout)
        print("Monitor alarm thread told to shutdown")  
        
# Thread to monitor sensors
class monitor_sensors(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.stoprequest = threading.Event()
        os.system('sudo modprobe w1-gpio')
        os.system('sudo modprobe w1-therm')

    def run(self):
        global alarmcode_q, smokeon, smokeoff, garagebutton 


        # General Setup
        #~ print("Sensor Thread starting")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM) 
        self.db = sqlite3.connect("./data/zhmmonitor.db", isolation_level=None)
        self.parmstab = zhmutils.parms(self.db)
        self.emailaddressestab = zhmutils.emailaddresses(self.db)
##        for em in self.emailaddressestab.get_all():
##            print ("email addresses",em[0],em[1])
        self.logtab = zhmutils.Log(self.db,"EventLog",None, self.parmstab.get_mailparms(),self.emailaddressestab.get_all(),_prod)
        self.logtab.newentry("Program start",self.logtab.INFO)
##        print("maxtemplog=",self.maxtemplogentries)
        
        
        # Setup to monitor smoke detector
        GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(5,GPIO.OUT,  pull_up_down=GPIO.PUD_DOWN)
        self.smokedetector_prevstatus = False
        self.smokedetectorstatustab = zhmutils.smokedetectorstatus(self.db)
        
        # Setup to monitor garage door
        #~ print("about to setup garagedoor button")
        #~ time.sleep(30)
        GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Garage door monitor
        GPIO.setup(17, GPIO.OUT,  initial=GPIO.HIGH) # Garage door button
        self.garagetimer = datetime.datetime(1990,1,1,0,2)
        self.garagedoor_prevtime = datetime.datetime(1990,1,1,0,1)
        self.garagedoor_prevstatus = -1
        self.garagedoor_blinking = False
        self.garagedoorstatustab = zhmutils.garagedoorstatus(self.db)
        
        # Setup for temperature monitoring
        self.maxtemplogentries = self.parmstab.get_maxtemplogentries()
        self.tempstatustab = zhmutils.tempstatus(self.db)
        self.triggersensors = self.parmstab.get_triggersensors()
        self.tempsensornames = self.parmstab.get_tempsensornames()
        self.mintemps = self.parmstab.get_mintemps()
        self.templogtab = zhmutils.TempLog(self.db,"TempLog")
        base_dir = '/sys/bus/w1/devices/'
        sensors = glob.glob(base_dir + '28*')
        self.temps=[-100,-100,-100]
        prevtime = datetime.datetime(1990,1,1,0,1)
        dologentry = True
        bad_sensor = [False,False,False]
        for index, item in enumerate(self.tempsensornames):
            if item == "":
                bad_sensor[index] = True
        #~ print("bad_sensor=",bad_sensor)
        tempalert = [False,False,False]
        sleepcount = 601
        
        # Setup to monitor alarm system
        alarm = False
        armed = False
        batterywarn = False
        zonenames = self.parmstab.get_zonenames()
        prevcode = 0x100
        self.panelstatustab = zhmutils.panelstatus(self.db)

        # Setup to monitor for new network devices
        self.networkdevicestab = zhmutils.networkdevices(self.db,"NetworkDevices")
    
        # Loop until requested to shutdown
        while not self.stoprequest.isSet():
            if sleepcount >= 600: # (60*10 minutes)
#            if sleepcount >= 00:  #(60*10 minutes) TESTING
                sleepcount = 0
                # Monitor for new network devices
                t_output = subprocess.check_output (["sudo","arp-scan","-l"])   #, ">","./data/arpscan.tmp"
                for line in t_output.decode(locale.getdefaultlocale()[1]).split("\n"):
                    if line.startswith("192"):
                        t_device = line.split("\t")
                        #~ print (t_device)
                        if len(t_device) >= 4:
                            t_device[3] = "*** " + t_device[3]
                        if self.networkdevicestab.testnewdevice(t_device):
                            #~ print ("new device",t_device)
                            self.logtab.newentry("New network device detected at " + t_device[0] + " (" + t_device[1] + ")", self.logtab.WARNING)
                #~ # Monitor temperature sensors
                curtime = datetime.datetime.now().replace(microsecond=0)
                #~ print ("curtiome=", curtime)
                postreading = False
                #~ print ("sensors=",len(sensors))
                for index, item in enumerate(sensors):
                    tempfile = open(item+"/w1_slave")
                    thetext = tempfile.read()
                    tempfile.close()
                    #~ print("crc=",thetext.split("\n")[0].split(" ")[11])
                    if thetext.split("\n")[0].split(" ")[11] == "YES":
                        tempdata = thetext.split("\n")[1].split(" ")[9]
                        temperature = round(float(tempdata[2:]) / 1000,1)
                    else:    
                        print ("Bad temp readng in sensor %d at %s:\n" % (index,curtime), thetext)
                        temperature = self.temps[index]
                    #~ if temperature < 0:
                        #~ print ("temp dump:", thetext)
                    #~ print ("temp=",temperature," index=",index)
                    if self.temps[index] == None:
                        self.temps[index] = -100.0
                        
                    if (index in self.triggersensors) and (abs(temperature - self.temps[index]) >= 2):
                        dologentry = True
                    elif curtime > (prevtime + datetime.timedelta(hours=1)):
                        dologentry = True
                    self.temps[index] = temperature
                    if (temperature < self.mintemps[index]) and (temperature != -100):
                        dologentry = True;
                        if not(tempalert[index]):
                            self.logtab.newentry("Temperature too low on sensor %s. Temperature is %.2f" % (self.tempsensornames[index],temperature),self.logtab.CRITICAL)
                            tempalert[index] = True
                    elif tempalert[index]:
                        self.logtab.newentry("Temperature back within normal range on sensor %s. Temperature is %.2f" % (self.tempsensornames[index],temperature),self.logtab.CRITICAL)
                        tempalert[index] = False
                self.tempstatustab.set_status([curtime]+self.temps)
                if dologentry:
                    self.templogtab.newentry(curtime,self.temps)
                    prevtime = curtime
                    dologentry = False
                #~ print("self.temps=",self.temps)
                for index, item in enumerate(self.temps):
                    if not(bad_sensor[index]) and (item == -100):
                        self.logtab.newentry("Bad temperature sensor reading on sensor: %s" % self.tempsensornames[index],self.logtab.INFO)
                        bad_sensor[index] = True
            else:
                sleepcount += 1
            # Monitor for alarm codes
            if (not(alarmcode_q.empty())):
                code = alarmcode_q.get()
                #~ print("have alarm code",code)
                if (code == 0x00):
                    if (alarm):
                        self.logtab.newentry("Alarm system is disarmed" ,self.logtab.CRITICAL)
                        alarm = False
                    else:
                        self.logtab.newentry("Alarm system is disarmed" ,self.logtab.INFO)
                    armed = False
                elif (code == 0x80):
                    self.logtab.newentry("Alarm system is ARMED" ,self.logtab.INFO)
                    armed = True
                else:
                    zones = [n for n in range(7) if (prevcode & (~code)) & 2**n]
                    #~ print("off Zones=",zones)
                    for zone in zones:
                        if (zone == 6):
                            self.logtab.newentry("Battery warning is cancelled",self.logtab.WARNING)
                            batterywarn = False
                        else:
                            self.logtab.newentry("Alarm off for zone: %s" % zonenames[zone],self.logtab.CRITICAL)
                    zones = [n for n in range(7) if (~prevcode & (code)) & 2**n]
                    #~ print("on Zones=",zones)
                    for zone in zones:
                        if (zone == 6):
                            self.logtab.newentry("Battery problem - needs to be replaced?",self.logtab.WARNING)
                            batterywarn = True
                        else:
                            self.logtab.newentry("ALARM Sounding for zone: %s" % zonenames[zone],self.logtab.CRITICAL)
                prevcode = code
                self.panelstatustab.set_status([datetime.datetime.now().replace(microsecond=0),armed,alarm,batterywarn,code])

            # Monitor smoke detector sounding
            if GPIO.input(27) != self.smokedetector_prevstatus:
                if GPIO.input(27): 
                    self.logtab.newentry("Smoke Alarm SOUNDING",self.logtab.CRITICAL)  
                else:
                    self.logtab.newentry("Smoke Alarm NOW Off",self.logtab.CRITICAL) 
                self.smokedetector_prevstatus = GPIO.input(27)
                self.smokedetectorstatustab.set_status([datetime.datetime.now().replace(microsecond=0),self.smokedetector_prevstatus])

            # Monitor garage door open/close
            if GPIO.input(22) != self.garagedoor_prevstatus:
                #~ print("Garage door callback invoked")
                if GPIO.input(22):     # if port 22 == 1
                    if (self.garagetimer == datetime.datetime(1990,1,1,0,1)):
                        self.logtab.newentry("Garage door is NOW closed",self.logtab.CRITICAL) # CRITICAL
                    elif (datetime.datetime.now() < (self.garagedoor_prevtime + datetime.timedelta(seconds=10))):
                        if not(self.garagedoor_blinking):
                            self.logtab.newentry("Garage door sensor is blinking - closed",self.logtab.WARNING)
                            self.garagedoor_blinking = True
                    else:
                        self.logtab.newentry("Garage door is closed",self.logtab.INFO)
                        self.garagedoor_blinking = False
                    self.garagetimer = datetime.datetime(1990,1,1,0,2)
                    #~ print ("Light is on")
                else:
                    if (datetime.datetime.now() < (self.garagedoor_prevtime + datetime.timedelta(seconds=10))):
                        if not(self.garagedoor_blinking):
                            self.logtab.newentry("Garage door sensor is blinking - opened",self.logtab.WARNING)
                            self.garagedoor_blinking = True
                    else:
                        self.logtab.newentry("Garage door is opened",self.logtab.INFO)
                        self.garagetimer = datetime.datetime.now()
                        self.garagedoor_blinking = False
                    #~ print ("Light is off")
                self.garagedoor_prevstatus = GPIO.input(22)
                self.garagedoorstatustab.set_status([datetime.datetime.now().replace(microsecond=0),self.garagedoor_prevstatus])
                self.garagedoor_prevtime = datetime.datetime.now()
                
            # Monitor garage door opened timer
            if self.garagetimer > datetime.datetime(1990,1,1,0,2):
                if (datetime.datetime.now() > (self.garagetimer + datetime.timedelta(minutes=10))):
                    self.garagetimer = datetime.datetime(1990,1,1,0,1)
                    self.logtab.newentry("Garage door has been opened for more than 10 minutes",self.logtab.CRITICAL)  # CRITICAL
            
            # Process Smoke on
            if smokeon:
                self.logtab.newentry("Smoke alarm set manually",self.logtab.WARNING) 
                GPIO.output(5,GPIO.HIGH)
                #~ print("gpio 5 set high")
                lock.acquire()
                smokeon = False
                lock.release()
            
            # Process Smoke off
            if smokeoff:
                GPIO.output(5,GPIO.LOW)
                #~ print("gpio 5 set low")
                lock.acquire()
                smokeoff = False
                lock.release()
            
            # Process Garage Door Button
            if garagebutton:
                self.logtab.newentry("Garage door button pressed manually",self.logtab.WARNING) 
                GPIO.output(17, GPIO.LOW)
                time.sleep(.5)
                GPIO.output(17, GPIO.HIGH)
                lock.acquire()
                garagebutton = False
                lock.release()
                
            time.sleep(1)
        # Main loop finished - cleanup and terminate
        self.parmstab.cleanup()
        self.emailaddressestab.cleanup()
        self.templogtab.cleanup()
        self.db.close()
        print("Sensor thread is ending")

    # If client says time to shutdown, tell the thread
    def join(self, timeout=None):
        self.stoprequest.set()
        time.sleep(5)
        super(monitor_sensors, self).join(timeout)
        print("Monitor sensors thread told to shutdown")  

###################################################################################################################
### start of main code

print ( 'Starting zhm service:',datetime.datetime.now().replace(microsecond=0), ' ',version_long)

if __name__ == "__main__":
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "p", ["prod"])
    except getopt.GetoptError:
        print ("gotopt error")
        sys.exit(2)
    global _prod, smokeon, smokeoff, garagebutton
    smokeon = False
    smokeoff = False
    garagebutton = False
 
    _prod = False
    for opt, arg in opts:                
        if opt in ('-p', "-prod"):
            _prod = True
    print("Production mode=",_prod)
    lock = threading.Lock()
    alarmcode_q = queue.Queue()

    monitor_sensors_thread = monitor_sensors(1)
    monitor_sensors_thread.start()
    monitor_alarm_system_thread = monitor_alarm_system(2)
    monitor_alarm_system_thread.start()

    address = ('localhost', 6000) 
    #~ print(address)    # family is deduced to be 'AF_INET'
    listener = Listener(address, authkey=b"secret password")
    conn = listener.accept()
    #~ print ("connmain=",conn)
    monitor_comm_thread = monitor_comm(3)
    monitor_comm_thread.start()
    #~ print ('connection accepted from', listener.last_accepted)
    #~ time.sleep(10)
    while True:
        try:
            #~ print("Waiting for data")
            msg = conn.recv()
            #~ print("Data=",msg)
        except:
            conn.close()
            conn = listener.accept()
            #~ print("Connection reset")
            msg = None
        if msg == 'close':
            conn.close()
            break
        elif msg == "Alive?":
            #~ print("Testing for alive")
            conn.send("Yup")
        elif msg == "SmokeOn":
            lock.acquire()
            smokeon = True
            lock.release()
            #~ print("Requesting Smoke On")
        elif msg == "SmokeOff":
            lock.acquire()
            smokeoff = True
            lock.release()
            #~ print("Requesting Smoke Off")
        elif msg == "GarageButton":
            #~ print("Requesting Garage Button")
            lock.acquire()
            garagebutton = True
            lock.release()
        #~ elif msg == "SendChar":
            #~ print("Sending character")
            #~ zhmalarm.sendchar(0x11);
        elif msg == None:
            print("No message")
    listener.close()
    monitor_alarm_system_thread.join()
    print("Monitor Alarm thread finished\n")
    monitor_sensors_thread.join()
    print("Monitor Sensor thread finished\n")
    monitor_comm_thread.join()
    print ( 'zhm Service Ended:', datetime.datetime.now().replace(microsecond=0), ' ',version_long)





