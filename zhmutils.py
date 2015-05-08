#!/usr/bin/python
#
# Copyright (C) Dwayne Zon 2015 <dwayne.zon@gmail.com> 
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation

import datetime
import sqlite3
from gi.repository import Gtk
from gi.repository import GObject

import smtplib
import email.utils
from email.mime.text import MIMEText

###################################################################################################################
# emailaddresses DB
###################################################################################################################
class emailaddresses():
    def __init__(self,db):
        self.name = "emailaddresses"
        self.dbc = db.cursor()
        # self.dbc.execute("drop table emainaddresses")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key,
                EmailAddress varchar(255),
                MsgLevel integer)
            """ % self.name)
        self.sql = "Insert into %s (EmailAddress, MsgLevel) VALUES (?, ?)" % (self.name)

    # Cleanup on close
    def cleanup(self):
        self.dbc.close()
       
    def get_all(self):
        self.dbc.execute("SELECT EmailAddress, MsgLevel FROM %s" % (self.name))
        self.store = Gtk.ListStore(str, int)
        self.rows = self.dbc.fetchall()
        for self.row in self.rows:
            # print"self.row",self.row[0],"'", self.row[1],"'")
            self.store.append(self.row)
        return self.store

    def set_all(self,liststore):
        self.dbc.execute("DELETE FROM %s" % (self.name))
        for self.row in liststore:
            self.dbc.execute(self.sql,tuple(self.row))

#################################################################################################################
# Define routines for panelstatus table
#################################################################################################################
class panelstatus():
        
    def __init__(self,db):
        self.dbc = db.cursor()
        self.name = "panelstatus"
        # self.dbc.execute("drop table panelstatus")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key,
                TimeStamp DateTime, 
                Armed Boolean,
                Alarmed Boolean,
                BatteryWarning Boolean,
                Zones Integer)
           """ % self.name)
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        if self.row == None:
            self.row = [datetime.datetime.now().replace(microsecond=0), False,False,False,0]
            self.dbc.execute("Insert into %s values (1, ?,?,?,?,?)" % (self.name),(self.row))
            self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
            self.row = self.dbc.fetchone()

# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Get Status from database
    def get_status(self):
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        return self.row

# Update field in table
    def set_status(self, newrow):
        self.dbc.execute("UPDATE %s SET TimeStamp=?, Armed=?, Alarmed=?, BatteryWarning=?, Zones=? Where Primekey = 1" % (self.name), (newrow))
        self.row = newrow

#################################################################################################################
# Define routines for garage door table
##############################################################################################################

class garagedoorstatus():
        
    def __init__(self,db):
        self.dbc = db.cursor()
        self.name = "garagedoorstatus"
        # self.dbc.execute("drop table garagedoorstatus")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key,
                TimeStamp DateTime, 
                Closed Boolean)
           """ % self.name)
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        if self.row == None:
            self.row = [datetime.datetime.now().replace(microsecond=0), False]
            self.dbc.execute("Insert into %s values (1, ?,?)" % (self.name),(self.row))
            self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
            self.row = self.dbc.fetchone()

# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Get Status from database
    def get_status(self):
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        return self.row

# Update field in table
    def set_status(self, newrow):
        self.dbc.execute("UPDATE %s SET TimeStamp=?, Closed=? Where Primekey = 1" % (self.name), (newrow))
        self.row = newrow

#################################################################################################################
# Define routines for smoke detector table
##############################################################################################################

class smokedetectorstatus():
        
    def __init__(self,db):
        self.dbc = db.cursor()
        self.name = "smokedetectorstatus"
        # self.dbc.execute("drop table smokedetectorstatus")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key,
                TimeStamp DateTime, 
                Sounding Boolean)
           """ % self.name)
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        if self.row == None:
            self.row = [datetime.datetime.now().replace(microsecond=0), False]
            self.dbc.execute("Insert into %s values (1, ?,?)" % (self.name),(self.row))
            self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
            self.row = self.dbc.fetchone()

# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Get Status from database
    def get_status(self):
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        return self.row

# Update field in table
    def set_status(self, newrow):
        self.dbc.execute("UPDATE %s SET TimeStamp=?, Sounding=? Where Primekey = 1" % (self.name), (newrow))
        self.row = newrow

#################################################################################################################
# Define routines for tempstatus table
#################################################################################################################

class tempstatus():
        
    def __init__(self,db):
        self.dbc = db.cursor()
        self.name = "tempstatus"
        # self.dbc.execute("drop table tempstatus")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key,
                TimeStamp DateTime, 
                Sensor1 Real,
                Sensor2 Real,
                Sensor3 Real)
           """ % self.name)
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        if self.row == None:
            self.row = [datetime.datetime.now().replace(microsecond=0), None, None, None]
            self.dbc.execute("Insert into %s values (1, ?,?,?,?)" % (self.name),(self.row))
            self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
            self.row = self.dbc.fetchone()

# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Get Status from database
    def get_status(self):
       self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
       self.row = self.dbc.fetchone()
       return self.row

# Update field in table
    def set_status(self, newrow):
        self.dbc.execute("UPDATE %s SET TimeStamp=?, Sensor1=?, Sensor2=?, Sensor3=? Where Primekey = 1" % (self.name), (newrow))
        self.row = newrow

##################################################################################################################
# Define routines for parms table
##################################################################################################################

class parms():
    def __init__(self,db):
        self.dbc = db.cursor()
        self.name = "parms"
        # self.dbc.execute("Drop table parms")

        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key,
                MinTemp1 Integer,               /* 1 */
                MinTemp2 Integer,               /* 2 */
                MinTemp3 Integer,               /* 3 */
                MaxLogEntries Integer,          /* 4 */
                MaxTempLogEntries Integer,      /* 5 */
                MailServer String,              /* 6 */
                MailPort String,                /* 7 */
                Userid String,                  /* 8 */
                Password String,                /* 9 */
                Sensor1Name String,             /* 10 */
                Sensor2Name String,
                Sensor3Name String,
                Zone1Name String,               /* 13 */
                Zone2Name String,
                Zone3Name String,
                Zone4Name String,
                Zone5Name String,
                Zone6Name String)
           """ % self.name)
        self.dbc.execute("SELECT * FROM %s Where Primekey = 1" % (self.name))
        self.row = self.dbc.fetchone()
        if self.row == None:
                self.row = (1,19, 20, 21, 10000,10000,"<Mail Server>", "<Port>", "<Userid>", "<Password>","*<Sensor 1 name>","<Sensor 2 name>","<Sensor 3 name>")
                for i in range(6):
                        self.row += ("<Zone " + str(i+1) + " name>",)
                self.dbc.execute("Insert into parms values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?, ?)", (self.row))

# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Get MinTemp from database
    def get_mintemps(self):
        return self.row[1:4]

# Get MaxLogEntries from database
    def get_maxlogentries(self):
        return self.row[4]

# Get MaxTempLogEntries from database
    def get_maxtemplogentries(self):
        return self.row[5]

# Get mail parms from database
    def get_mailparms(self):
        return self.row[6:10]
        
# Get temperature sensor names
    def get_tempsensornames(self):
        return self.row[10:13]

# Get ZoneName from database
    def get_zonenames(self):
        return self.row[13:]

# Get all parms from database
    def get_allparms(self):
        return self.row
        
# Get trigger sensor (the ones that starts with an asterisk) that will cause temperatures to log if the temperature change is more than 2 degress
    def get_triggersensors(self):
        i = [x for x, item in enumerate(self.row[10:13]) if item.startswith('*')]
        if i:
            return i
        else:
            return [0]

# Update all parms in table
    def set_allparms(self, newrow):
        self.dbc.execute("""UPDATE parms SET  MinTemp1=?, MinTemp2 = ?, MinTemp3 = ?, MaxLogEntries=?, MaxTempLogEntries=?, MailServer=?,
                        MailPort=?, Userid=?, Password=?, Sensor1Name=?, Sensor2Name=?, Sensor3Name=?, Zone1Name=?, Zone2Name=?,
                        Zone3Name=?, Zone4Name=?, Zone5Name=?, Zone6Name =? Where Primekey = 1""", (newrow[1:]))
        self.row = newrow

###################################################################################################################
# Temperature Logging DB
###################################################################################################################

class TempLog(GObject.GObject, Gtk.TreeModel):
    def __init__(self, db, table, maxentries=None):
        super(TempLog, self).__init__()
        self.name = table
        self.dbc = db.cursor()
##        self.dbc.execute("Drop Table TempLog")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key autoincrement,
                TimeStamp DateTime,
                Sensor1 Real,
                Sensor2 Real,
                Sensor3 Real)
           """ % self.name)
        self.primekeycache = []
        self.load_cache()
        if maxentries:
            if len(self.primekeycache) > maxentries:
                self.dbc.execute("DELETE FROM %s WHERE Primekey <=%d" % (self.name, self.primekeycache[maxentries]))

##        self.newentry(datetime.datetime.now().replace(microsecond=0),[100, 200, 300])
 
# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Return the column names
    def get_column_names(self):
        return (("Primekey", "TimeStamp", "Sensor1","Sensor2","Sensor3"))

# Returns the Gtk.TreeModelFlags for the Gtk.TreeModel implementation. The Gtk.TreeIter data is derived from
#       the database primekey for records and therefore is persistant across row deletion and inserts.
    def do_get_flags(self):
        return Gtk.TreeModelFlags.LIST_ONLY| Gtk.TreeModelFlags.ITERS_PERSIST

# Returns the number of columns found in the table metadata.
    def do_get_n_columns(self):
        return 5

# Return Column type
    def do_get_column_type(self, index):
##        print("indexbefore=",index)
        if index == 0:
            return int
        elif index == 1:
            return str
        else:
##            print("index=",index)
            return float

# Get records from database
    def _get_rows(self,sql,args=()):
        self.dbc.execute(sql,args)
        for self.raw in self.dbc: 
            yield self.raw 

# Get one records from database
    def _get_row(self,sql,args=()):
        for i in self._get_rows(sql,args):
##            print (i)
            return i

# Traslates a Gtk.TreePath to a Gtk.TreeIter. This is done by finding the primekey for the row in the database at the same
#       offset as the path.
    def do_get_iter(self, path):
        # print ("do_get_iter called; path = %s" % (path))
        self.row = self._get_row("SELECT * FROM %s ORDER BY Primekey DESC LIMIT 1 OFFSET %d" % (self.name,path[0]))
        iterator = Gtk.TreeIter()
        if path[0] < len(self.primekeycache):
            iterator.user_data = self.primekeycache[path[0]]
            # print ("returning true")
            return (True, iterator)
        else:
            # print ("returning false")
            return (False, iterator)

# Returns the rowrefs offset in the table which is used to generate the Gtk.TreePath.
    def do_get_path(self, iterator):
        # print ("do_get_path called; iter  = %s" % (iter))
        if iterator.user_data is not None:
            path = Gtk.TreePath(iterator.user_data)
            return path
        else:
            return None

            # Returns the data for a rowref at the givin column.
# Parameters:
#       rowref -- the rowref passed back in the on_get_iter method.
#       column -- the integer offset of the column desired.
    def do_get_value(self, iterator, column_index):
        # print ("do_get_value called; iterator = %s, column_index = %s"%(iterator, column_index))
        if iterator.user_data != self.row[0]:
            self.dbc.execute("SELECT * FROM %s WHERE Primekey = %d" % (self.name, iterator.user_data))
            self.row = self.dbc.fetchone()
##        print ("colument_index",column_index,self.row[column_index],self.row)
        if column_index > 4:
            return None
        else:
            return self.row[column_index]

# Load cache
    def load_cache(self):
        self.primekeycache = [r for (r,) in self._get_rows("SELECT Primekey FROM %s ORDER BY Primekey DESC" % (self.name,))]

# Returns the next Primekey found in the sqlite table.
# Parameters:
#       rowref -- the PrimeKey of the current iter.
    def do_iter_next(self, iterator):
        # print ("do_iter_next_called; iterator = %d"%(iterator.user_data))
        nextiter = self._get_offset(iterator.user_data) + 1
        if nextiter >= len(self.primekeycache):
            return False
        else:
            iterator.user_data = self.primekeycache[nextiter]
            return True

# Always returns False as List based TreeModels do not have children.
    def do_iter_has_child(self, iterator):
        return False

# Returns the primekey of the nth child from rowref. This will only return a value if rowref is None, which is the root node.
# Parameters:
#       rowref -- the primekey of the row.
#       n -- the row offset to retrieve.
    def do_iter_nth_child(self, iterator, index):
        # print ("do_iter_nth_child called; iterator = %s, index = %s" % (iterator, index))
        output_iterator = Gtk.TreeIter()
        output_iterator.user_data = index
        return (True, output_iterator)

    # Always returns None as lists do not have parent nodes.
    def do_iter_parent(self, child):
        return None

    # Delete a record
    def _delete_record(self,iter):
        self.row_deleted (self.get_path(iter))
        self.dbc.execute("DELETE FROM %s WHERE Primekey = %d" % (self.name, self.get_value(iter,0)))

    # Insert a new row (add button pushed)
    def newentry(self, timestamp, sensorvalues):
##        print("time log new entry")
        sql = "Insert into %s VALUES (?, ?, ?, ?, ?)" % (self.name)
        if self.primekeycache ==[]:
            newprimekey = 1
        else:
            newprimekey = max(self.primekeycache) + 1
        self.primekeycache.append(newprimekey)
        self.dbc.execute(sql,([newprimekey,timestamp] + sensorvalues))
        path = [len(self.primekeycache)-1,]
        self.row_inserted(path, self.get_iter(path))
            # print ("newentry/delete",len(self.primekeycache),len(self.primekeycache)-self.maxentries,self.primekeycache[len(self.primekeycache)-self.maxentries])

    # Update field in table
    def _set_value(self, rowref, column, newvalue):
        primekey = self.get_value(rowref,0)
        sql = "UPDATE %s SET %s = ?, Where Primekey = ?" % (self.name,column)
        self.dbc.execute(sql, (newvalue, primekey))
        path = (self._get_offset(primekey),)
        self.row_changed(path, rowref)


# Get offset of Primekey                         
    def _get_offset(self, primekey):
        if not len(self.primekeycache):
            self.load_cache()
        try:
            return self.primekeycache.index(primekey)
        except:
            return -1
###################################################################################################################
# Network Device DB
###################################################################################################################

class networkdevices(GObject.GObject, Gtk.TreeModel):
    def __init__(self, db, table):
        self.debug=False
        super(networkdevices, self).__init__()
        self.name = table
        self.dbc = db.cursor()
##        self.dbc.execute("Drop Table NetworkDevices")
        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                MacAddress VARCHAR(17) primary key,
                TimeStamp DateTime,
                IpAddress VARCHAR(15),
                Comment VARCHAR(255))
           """ % self.name)
        self.primekeycache = []
        self.load_cache()
 
# Cleanup on close
    def cleanup(self):
        self.dbc.close()

# Return the column names
    def get_column_names(self):
        return (("MacAddress", "TimeStamp", "IpAddress", "Comment"))

# Returns the Gtk.TreeModelFlags for the Gtk.TreeModel implementation. The Gtk.TreeIter data is derived from
#       the database primekey for records and therefore is persistant across row deletion and inserts.
    def do_get_flags(self):
        return Gtk.TreeModelFlags.LIST_ONLY| Gtk.TreeModelFlags.ITERS_PERSIST

# Returns the number of columns found in the table metadata.
    def do_get_n_columns(self):
        return 4

# Return Column type
    def do_get_column_type(self, index):
        return str

# Get records from database
    def _get_rows(self,sql,args=()):
        self.dbc.execute(sql,args)
        for self.raw in self.dbc: 
            yield self.raw 

# Get one records from database
    def _get_row(self,sql,args=()):
        for i in self._get_rows(sql,args):
            return i

# Traslates a Gtk.TreePath to a Gtk.TreeIter. This is done by finding the primekey for the row in the database at the same
#       offset as the path.
    def do_get_iter(self, path):
        # print ("do_get_iter called; path = %s" % (path))
        self.row = self._get_row("SELECT * FROM %s LIMIT 1 OFFSET %d" % (self.name,path[0]))
        iterator = Gtk.TreeIter()
        if path[0] < len(self.primekeycache):
            iterator.user_data = path[0]
            return (True, iterator)
        else:
            return (False, iterator)

# Returns the rowrefs offset in the table which is used to generate the Gtk.TreePath.
    def do_get_path(self, iterator):
        if iterator.user_data is not None:
            path = Gtk.TreePath(iterator.user_data)
            if self.debug:
                print("path",path)
            return path
        else:
            return None

# Returns the data for a rowref at the givin column.
# Parameters:
#       rowref -- the rowref passed back in the on_get_iter method.
#       column -- the integer offset of the column desired.
    def do_get_value(self, iterator, column_index):
        if self.debug:
            print (self.primekeycache[iterator.user_data])
            print (self.row)
        if self.primekeycache[iterator.user_data] != self.row[0]:
            self.dbc.execute('SELECT * FROM %s WHERE MacAddress = "%s"' % (self.name, self.primekeycache[iterator.user_data]))
            self.row = self.dbc.fetchone()
##        print ("colument_index",column_index,self.row[column_index],self.row)
        if column_index > 3:
            return None
        else:
            return self.row[column_index]

# Load cache
    def load_cache(self):
        self.primekeycache = [r for (r,) in self._get_rows('SELECT MacAddress FROM "%s" ORDER BY MacAddress' % (self.name,))]
        #~ print ("primekeycache\n", self.primekeycache)
# Returns the next Primekey found in the sqlite table.
# Parameters:
#       rowref -- the PrimeKey of the current iter.
    def do_iter_next(self, iterator):
        #~ print ("do_iter_next_called; iterator = %d max =%d"%(iterator.user_data,len(self.primekeycache)))
        nextiter = iterator.user_data + 1
        if nextiter >= len(self.primekeycache):
            return False
        else:
            iterator.user_data = nextiter
            return True

# Always returns False as List based TreeModels do not have children.
    def do_iter_has_child(self, iterator):
        return False

# Returns the primekey of the nth child from rowref. This will only return a value if rowref is None, which is the root node.
# Parameters:
#       rowref -- the primekey of the row.
#       n -- the row offset to retrieve.
    def do_iter_nth_child(self, iterator, index):
        # print ("do_iter_nth_child called; iterator = %s, index = %s" % (iterator, index))
        output_iterator = Gtk.TreeIter()
        output_iterator.user_data = index
        return (True, output_iterator)

    # Always returns None as lists do not have parent nodes.
    def do_iter_parent(self, child):
        return None

    # Delete a record
    def delete_record(self,iter):
        #~ print("iter=",self.get_value(iter,0))
        self.dbc.execute('DELETE FROM %s WHERE MacAddress = "%s"' % (self.name, self.get_value(iter,0)))
        #~ self.debug = True
        del self.primekeycache[iter.user_data]
        self.row_deleted (self.get_path(iter))

    # Test if device is already in the database - add it not
    def testnewdevice(self, t_device):
        if self._get_offset(t_device[1]) >= 0:
            sql = 'UPDATE %s SET TimeStamp = ?, IpAddress=? Where MacAddress = "%s"' % (self.name,t_device[1])
            self.dbc.execute(sql, (datetime.datetime.now().replace(microsecond=0), t_device[0]))
            return False
        else:
            sql = "Insert into %s VALUES (?, ?, ?, ?)" % (self.name)
            self.dbc.execute(sql, (t_device[1],datetime.datetime.now().replace(microsecond=0), t_device[0],t_device[2]))
            self.load_cache()
            return True

    # Update field in table
    def set_value(self, rowref, column, newvalue):
        primekey = self.get_value(rowref,0)
        sql = 'UPDATE %s SET %s = ? Where MacAddress = "%s"' % (self.name,column,primekey)
        #~ print (sql)
        self.dbc.execute(sql, (newvalue,))
        path = (self._get_offset(primekey),)
        self.row_changed(path, rowref)


# Get offset of Primekey                         
    def _get_offset(self, primekey):
        if not len(self.primekeycache):
            self.load_cache()
        try:
            return self.primekeycache.index(primekey)
        except:
            return -1


###################################################################################################################
# Log DB
###################################################################################################################
class Log(GObject.GObject, Gtk.TreeModel):
    INFO = 0
    WARNING = 1
    CRITICAL = 2
    def __init__(self, db, table, maxentries=None, mailparms=None,toaddresses=None,prod=True):
##        print ("initi starting")
        super(Log, self).__init__()
        self.name = table
        self.dbc = db.cursor()
        #~ self.dbc.execute("drop table EventLog")

        self.dbc.execute("""
            create table IF NOT EXISTS %s (
                PrimeKey integer primary key autoincrement,
                MsgLevel integer,
                TimeStamp DateTime,
                EventText Varchar(255))
           """ % self.name)
        self.primekeycache = []
        self.load_cache()
        if maxentries:
            if len(self.primekeycache) > maxentries:
                self.dbc.execute("DELETE FROM %s WHERE Primekey <=%d" % (self.name, self.primekeycache[maxentries]))
                self.load_cache()
           

# Do setup with parameters
    # def setparms(maxentries, mailserver, port, userid, password,toaddresses):
        self.maxentries = maxentries
        # print ("mailserver",mailserver)
        if mailparms and prod:
            self.mailserver = mailparms[0]
            self.port = mailparms[1]
            self.userid = mailparms[2]
            self.password = mailparms[3]
        else:
            self.mailserver = None
        self.toaddresses = toaddresses
        #~ print("toaddressen")
        #~ for row in self.toaddresses:
            #~ print (row[:])
##        print ("init ending")
        
# Send email routine
    def sendmail(self,message,msglevel):
        if self.mailserver:
            # print ("sendmail",msglevel)
            # print (self.toaddresses[0,0])
            # toaddressesfilter = self.toaddresses.filter_new()
            # toaddressesfilter.set_visible_func(self.toaddressfilterfunction)
##            for em in self.toaddresses:
##                print ("email addresses",em[0],em[1])

            toaddr = ','.join([emailaddress[0] for emailaddress in self.toaddresses if emailaddress[1] <= msglevel])
            #~ print("toaddr=",toaddr,msglevel)
            # print ("toaddresses",toaddr)
            if toaddr:
                msg = MIMEText("") # parms is body
                msg['To'] = toaddr
                msg['From'] = email.utils.formataddr(('zHome Monitoring', self.userid))
                msg['Subject'] = message
                try:
                    smtpObj = smtplib.SMTP(self.mailserver,self.port) #587
                    smtpObj.login(self.userid, self.password)
                    smtpObj.sendmail(self.userid, msg["To"].split(","), msg.as_string())
                except:
                    print("exception on email send attempt - ",sys.exc_info()[0])
                    return False
        return True

# Cleanup on close
    def cleanup(self):
        self.newentry("Ending Program",Log.INFO)
        self.dbc.close()

# Return the column names
    def get_column_names(self):
        # print ("get col names")
        return (("Primekey", "MsgLevel", "TimeStamp", "EventText"))

# Returns the Gtk.TreeModelFlags for the Gtk.TreeModel implementation. The Gtk.TreeIter data is derived from
#       the database primekey for records and therefore is persistant across row deletion and inserts.
    def do_get_flags(self):
        # print ("get flags")
        return Gtk.TreeModelFlags.LIST_ONLY| Gtk.TreeModelFlags.ITERS_PERSIST


# Returns the number of columns found in the table metadata.
    def do_get_n_columns(self):
        # print ("get n cols")

        return 4

# Return Column type
    def do_get_column_type(self, index):
        # print ("get col tyu[e")
        if index <= 1:
            return int
        else:
            return str

# Get records from database
    def _get_rows(self,sql,args=()):
        # print ("get rows")
        self.dbc.execute(sql,args)
        for self.raw in self.dbc: 
            yield self.raw 

# Get one records from database
    def _get_row(self,sql,args=()):
##        print ("get row")
        
        for i in self._get_rows(sql,args): 
            return i

# Traslates a Gtk.TreePath to a Gtk.TreeIter. This is done by finding the primekey for the row in the database at the same
#       offset as the path.
    def do_get_iter(self, path):
        # print ("do_get_iter called; path = %s" % (path))
        self.row = self._get_row("SELECT * FROM %s ORDER BY Primekey DESC LIMIT 1 OFFSET %d" % (self.name,path[0]))
        iterator = Gtk.TreeIter()
        if path[0] < len(self.primekeycache):
            iterator.user_data = self.primekeycache[path[0]]
            return (True, iterator)
        else:
            return (False,iterator)

# Returns the rowrefs offset in the table which is used to generate the Gtk.TreePath.
    def do_get_path(self, iterator):
        # print ("do_get_path called; iter  = %s" % (iter))
        if iterator.user_data is not None:
            path = Gtk.TreePath(iterator.user_data)
            return path
        else:
            return None

            # Returns the data for a rowref at the givin column.
# Parameters:
#       rowref -- the rowref passed back in the on_get_iter method.
#       column -- the integer offset of the column desired.
    def do_get_value(self, iterator, column_index):
        #~ print ("do_get_value called; iterator = %s, column_index = %s"%(iterator, column_index))
        #~ print ("row0=",self.row[0])
        if iterator.user_data != self.row[0]:
            self.dbc.execute("SELECT * FROM %s WHERE Primekey = %d" % (self.name, iterator.user_data))
            self.row = self.dbc.fetchone()
        if column_index > 4:
            return None
        else:
            return self.row[column_index]

# Load cache
    def load_cache(self):
        self.primekeycache = [r for (r,) in self._get_rows("SELECT Primekey FROM %s ORDER BY Primekey DESC" % (self.name,))]

# Returns the next Primekey found in the sqlite table.
# Parameters:
#       rowref -- the PrimeKey of the current iter.
    def do_iter_next(self, iterator):
        # print ("do_iter_next_called; iterator = %d"%(iterator.user_data))
        nextiter = self._get_offset(iterator.user_data) + 1
        if nextiter >= len(self.primekeycache):
            return False
        else:
            iterator.user_data = self.primekeycache[nextiter]
            return True

# Always returns False as List based TreeModels do not have children.
    def do_iter_has_child(self, iterator):
        return False

# Returns the primekey of the nth child from rowref. This will only return a value if rowref is None, which is the root node.
# Parameters:
#       rowref -- the primekey of the row.
#       n -- the row offset to retrieve.
    def do_iter_nth_child(self, iterator, index):
        # print ("do_iter_nth_child called; iterator = %s, index = %s" % (iterator, index))
        output_iterator = Gtk.TreeIter()
        output_iterator.user_data = index
        return (True, output_iterator)

    # Always returns None as lists do not have parent nodes.
    def do_iter_parent(self, child):
        return None

    # Delete a record
    def _delete_record(self,iter):
        self.row_deleted (self.get_path(iter))
        self.dbc.execute("DELETE FROM %s WHERE Primekey = %d" % (self.name, self.get_value(iter,0)))

    # Insert a new row (add button pushed)
    def newentry(self,newentrytext,msglevel):
##        print("new entry")
        sql = "Insert into %s VALUES (?, ?, ?, ?)" % (self.name)
        if self.primekeycache ==[]:
            self.newprimekey = 1
        else:
            self.newprimekey = max(self.primekeycache) + 1
##        print (self.newprimekey)
##        print("new PRIME key=",self.newprimekey)
        self.primekeycache.append(self.newprimekey)
        self.dbc.execute(sql,(self.newprimekey, msglevel, datetime.datetime.now().replace(microsecond=0), newentrytext))
        path = [len(self.primekeycache)-1,]
        rowref = self.get_iter([len(self.primekeycache)-1,])
        self.row_inserted(path, rowref)
        if not self.sendmail(newentrytext,msglevel):
            if self.primekeycache ==[]:
                self.newprimekey = 1
            else:
                self.newprimekey = max(self.primekeycache) + 1
            self.primekeycache.append(self.newprimekey)
            self.dbc.execute(sql,(self.newprimekey, self.CRITICAL, datetime.datetime.now().replace(microsecond=0), "Error Trying to send email"))
            path = [len(self.primekeycache)-1,]
            rowref = self.get_iter([len(self.primekeycache)-1,])
            self.row_inserted(path, rowref)

    # Update field in table
    def _set_value(self, rowref, column, newvalue):
        if column != 3:
            return
        primekey = self.get_value(rowref,0)
        sql = "UPDATE %s SET EventText = ?, Where Primekey = ?" % (self.name)
        self.dbc.execute(sql, (newvalue, primekey))

# Get offset of Primekey                         
    def _get_offset(self, primekey):
        if not len(self.primekeycache):
            self.load_cache()
        try:
            return self.primekeycache.index(primekey)
        except:
            return -1
