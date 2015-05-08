#!/usr/bin/python
license=""" 
Copyright (C) Dwayne Zon 2015 <dwayne.zon@gmail.com> 

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation
""" 
version_long='V1.0: <2015-01-09>'
program_name='zhomemonitor'
version_short='V1.0'
t_green='<span foreground="green">'
t_red='<span foreground="red">'
t_black='<span foreground="black">'
t_blue='<span foreground="blue">'
t_yellow='<span background="yellow" font_weight="bold">'
t_endspan='</span>'
keypadcodes=[0x21,0x48, 0x28, 0x18, 0x44, 0x24, 0x14, 0x42, 0x22,  0x12]


import datetime
import sqlite3
import zhmutils # zhm db interface
from gi.repository import Gtk, Gdk
from gi.repository import GObject
from multiprocessing.connection import Client
from array import array
import os
import sys
import csv
import socket

def msgbox(msgtext):
    dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,Gtk.ButtonsType.OK, msgtext)
    dialog.run()
    dialog.destroy()

class windowmain:
    def __init__(self):
        self.builder = Gtk.Builder() 
        self.builder.add_from_file("zhomemonitor.glade")
        self.window = self.builder.get_object("windowmain")
        # if (self.window):
        self.window.connect("destroy", Gtk.main_quit)
        self.window.set_default_size(905,690)
        self.builder.connect_signals(self)
        self.keypadbuffer = ""
        self.conn = None
        
        # Set fields in the preferences tab
        self.parmstab = zhmutils.parms(db)
        self._parms = self.parmstab.get_allparms()
        self.entrymintemp1 = self.builder.get_object("entrymintemp1")
        self.entrymintemp2 = self.builder.get_object("entrymintemp2")
        self.entrymintemp3 = self.builder.get_object("entrymintemp3")
        self.entrymaxlog = self.builder.get_object("entrymaxlog")
        self.entrymaxtemplog = self.builder.get_object("entrymaxtemplog")
        self.entryzone1name = self.builder.get_object("entryzone1name")
        self.entryzone2name = self.builder.get_object("entryzone2name")
        self.entryzone3name = self.builder.get_object("entryzone3name")
        self.entryzone4name = self.builder.get_object("entryzone4name")
        self.entryzone5name = self.builder.get_object("entryzone5name")
        self.entryzone6name = self.builder.get_object("entryzone6name")
        self.entrymailserver = self.builder.get_object("entrymailserver")
        self.entryport = self.builder.get_object("entryport")
        self.entryuserid = self.builder.get_object("entryuserid")
        self.entrypassword = self.builder.get_object("entrypassword")
        self.entrytempsensor1 = self.builder.get_object("entrytempsensor1")
        self.entrytempsensor2 = self.builder.get_object("entrytempsensor2")
        self.entrytempsensor3 = self.builder.get_object("entrytempsensor3")
        self.buttonservice = self.builder.get_object("buttonservice")
        self.entrymintemp1.set_text(str(self._parms[1]))
        self.entrymintemp2.set_text(str(self._parms[2]))
        self.entrymintemp3.set_text(str(self._parms[3]))
        self.entrymaxlog.set_text(str(self._parms[4]))
        self.entrymaxtemplog.set_text(str(self._parms[5]))
        self.entrymailserver.set_text(str(self._parms[6]))
        self.entryport.set_text(str(self._parms[7]))
        self.entryuserid.set_text(str(self._parms[8]))
        self.entrypassword.set_text(str(self._parms[9]))
        self.entrytempsensor1.set_text(str(self._parms[10]))
        self.entrytempsensor2.set_text(str(self._parms[11]))
        self.entrytempsensor3.set_text(str(self._parms[12]))
        self.entryzone1name.set_text(self._parms[13])
        self.entryzone2name.set_text(self._parms[14])
        self.entryzone3name.set_text(self._parms[15])
        self.entryzone4name.set_text(self._parms[16])
        self.entryzone5name.set_text(self._parms[17])
        self.entryzone6name.set_text(self._parms[18])

        # Set email addresses in preferences tab
        self.emailaddressestab = zhmutils.emailaddresses(db)
        self.emailaddressesstore = self.emailaddressestab.get_all()
        rend_email = Gtk.CellRendererText()
        self.treeviewemailaddresses = self.builder.get_object("treeviewemailaddresses")
        self.treeviewemailaddresses.set_reorderable(True) 
        col_email = Gtk.TreeViewColumn('Email Address', rend_email, text=0)
        self.treeviewemailaddresses.append_column(col_email)
        self.msglevels = Gtk.ListStore(str)
        self.msglevels.append(["INFO",])
        self.msglevels.append(["WARNING",])
        self.msglevels.append(["CRITITCAL",])
        rend_msglevel = Gtk.CellRendererText()
        col_msglevel = Gtk.TreeViewColumn('Msg Level', rend_msglevel, text=1)
        col_msglevel.set_cell_data_func(rend_msglevel,self.format_msglevel)
        self.treeviewemailaddresses.append_column(col_msglevel)
        self.treeviewemailaddresses.set_model(self.emailaddressesstore)
        self.treeviewemailaddresses.connect('row-activated', self.emailaddresses_row_select,self.emailaddressesstore)
        
        # Set fields on main panel
        self.tempstatustab = zhmutils.tempstatus(db)
        self.panelstatustab = zhmutils.panelstatus(db)
        self.garagedoorstatustab = zhmutils.garagedoorstatus(db)
        self.smokedetectorstatustab = zhmutils.smokedetectorstatus(db)
        self.labelserviceerrormsg = self.builder.get_object("labelserviceerrormsg")
        self.labeltemptimestamp = self.builder.get_object("labeltemptimestamp")
        self.labelsensor1 = self.builder.get_object("labelsensor1")       
        self.labelsensor2 = self.builder.get_object("labelsensor2")       
        self.labelsensor3 = self.builder.get_object("labelsensor3")       
        self.labelsensor1.set_label(self.entrytempsensor1.get_text())
        self.labelsensor2.set_label(self.entrytempsensor2.get_text())
        self.labelsensor3.set_label(self.entrytempsensor3.get_text())
        self.labelsensor1value = self.builder.get_object("labelsensor1value")       
        self.labelsensor2value = self.builder.get_object("labelsensor2value")       
        self.labelsensor3value = self.builder.get_object("labelsensor3value")
        self.labelserviceerrormsg.override_color(Gtk.StateType.NORMAL, Gdk.RGBA(1,0,0,.9))
        self.labelstatus = self.builder.get_object("labelstatus")
        self.labelbattery = self.builder.get_object("labelbattery")
        self.labelzones = []
        for i in range(1,7):
            self.labelzones.append(self.builder.get_object("labelzone%s" % (i,)))       
        self.labelpaneldatetime = self.builder.get_object("labelpaneldatetime")
        self.labelgaragedoor = self.builder.get_object("labelgaragedoor")
        self.labelsmokedetector = self.builder.get_object("labelsmokedetector")
        self.labelgddatetime = self.builder.get_object("labelgddatetime")
        
        # Set up log messages in Log tab
        self.logtab = zhmutils.Log(db,"EventLog",self.parmstab.get_maxlogentries())
        self.viewlog = self.builder.get_object("viewlog")
        rend_timestamp = Gtk.CellRendererText()
        col_timestamp = Gtk.TreeViewColumn('Time Stamp', rend_timestamp, text=2)
        col_timestamp.set_cell_data_func(rend_timestamp,self.format_logcell,2)
        self.viewlog.append_column(col_timestamp)
        rend_eventtext = Gtk.CellRendererText()
        col_Eventtext = Gtk.TreeViewColumn('Event', rend_eventtext, text=3)
        col_Eventtext.set_cell_data_func(rend_eventtext,self.format_logcell,3)
        self.viewlog.append_column(col_Eventtext)
        self.viewlog.set_model(self.logtab)
        
        # Set up temperature log messages in Temperature Log tab
        self.templogtab = zhmutils.TempLog(db,"TempLog",self.parmstab.get_maxtemplogentries())
        self.viewtemplog = self.builder.get_object("viewtemplog")
        rend_temptimestamp = Gtk.CellRendererText()
        col_temptimestamp = Gtk.TreeViewColumn('Time Stamp', rend_temptimestamp, text=1)
        self.viewtemplog.append_column(col_temptimestamp)
        rend_tempsensor1 = Gtk.CellRendererText()
        col_TempSensor1 = Gtk.TreeViewColumn(self.entrytempsensor1.get_text(), rend_tempsensor1, text=2)
        col_TempSensor1.set_cell_data_func(rend_tempsensor1,self.format_temperature,2)
        self.viewtemplog.append_column(col_TempSensor1)
        rend_tempsensor2 = Gtk.CellRendererText()
        col_TempSensor2 = Gtk.TreeViewColumn(self.entrytempsensor2.get_text(), rend_tempsensor2, text=3)
        col_TempSensor2.set_cell_data_func(rend_tempsensor2,self.format_temperature,3)
        self.viewtemplog.append_column(col_TempSensor2)
        rend_tempsensor3 = Gtk.CellRendererText()
        col_TempSensor3 = Gtk.TreeViewColumn(self.entrytempsensor3.get_text(), rend_tempsensor3, text=4)
        col_TempSensor3.set_cell_data_func(rend_tempsensor3,self.format_temperature,4)
        self.viewtemplog.append_column(col_TempSensor3)
        self.viewtemplog.set_model(self.templogtab)
        
        # Set up Network Devices on the network device tab
        self.netdevtab = zhmutils.networkdevices(db,"NetworkDevices")
        self.viewnetdev = self.builder.get_object("viewnetworkdevices")
        rend_macaddr = Gtk.CellRendererText()
        col_macaddr = Gtk.TreeViewColumn("MAC address", rend_macaddr, text=0)
        self.viewnetdev.append_column(col_macaddr)
        rend_temptimestamp = Gtk.CellRendererText()
        col_temptimestamp = Gtk.TreeViewColumn('Time Stamp', rend_temptimestamp, text=1)
        self.viewnetdev.append_column(col_temptimestamp)
        rend_ipaddr = Gtk.CellRendererText()
        col_ipaddr = Gtk.TreeViewColumn("IP Address", rend_ipaddr, text=2)
        self.viewnetdev.append_column(col_ipaddr)
        rend_comment = Gtk.CellRendererText()
        col_comment = Gtk.TreeViewColumn("Comment", rend_comment, text=3)
        self.viewnetdev.append_column(col_comment)
        self.viewnetdev.set_model(self.netdevtab)
        self.viewnetdev.connect('row-activated', self.netdev_row_select,self.netdevtab)
                
        # Launch Window
        # self.window.fullscreen()
        self.on_buttonrefresh_clicked(None)
        self.window.show_all()

    # Process global signals
    def on_buttonclose_clicked(self, widget):
        self.parmstab.cleanup
        self.emailaddressestab.cleanup
        self.window.destroy()
        Gtk.main_quit()
        
    # Smoke Detector Alarm
    def on_togglesmokealarm_toggled(self,widget):
        #~ print("toggle smoke detector")
        if self.conn:
            #~ print("self conn")
            if widget.get_active():
                dialog=Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL,
                    'Are you sure you want turn on the smoke alarms?')
                r=dialog.run()
                dialog.destroy()
                if r == Gtk.ResponseType.OK:
                    self.conn.send("SmokeOn")
            else:
                self.conn.send("SmokeOff")
        else:
            msgbox("** ERROR ** Service not active")
    
    # Garage door button
    def on_buttongarage_clicked(self, widget):
        dialog=Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL,
                                    'Are you sure you want press the garage OH door button?')
        r=dialog.run()
        dialog.destroy()
        if r == Gtk.ResponseType.OK:
            #~ print ("Garage door button pressed")
                    #~ print("service active clicked")
            if self.conn:
                self.conn.send("GarageButton")
                msgbox("Garage Button Pressed")
            else:
                msgbox("** ERROR ** Service not active")

    #About dialog box
    def on_buttonabout_clicked(self, widget):
        d=Gtk.AboutDialog()
        d.set_program_name(program_name)
        d.set_version(version_short)
        d.set_comments('Zon Home Monitoring System')
        d.set_authors(['Dwayne Zon <dwayne.zon@gmail.com'])
        d.set_license(license)
        d.set_website('https://docs.google.com/document/d/1toyMh69KyL-EzT-nRC9gl0Y8e-3dpsEDmgOBxEW1XmM/pub')    
        d.connect('response', lambda d, r: d.destroy())
        d.run()

    # Switching notebook page            
    def on_notebooktabs_switch_page(self,zipnotebook, page, page_num):
        #~ print("switching to page", page_num)
        if (page_num == 1):
            self.templogtab.load_cache()
        elif (page_num == 2):
            self.logtab.load_cache()
        elif (page_num == 4):
            self.netdevtab.load_cache()
        

# DEBUG - TESTING
    def on_buttondebug_clicked(self, widget):
        #~ self.conn.send("SendChar")
        print("sending char")

    # Process signals from main tab
    def on_buttonsend_clicked(self, widget):
#        Translate characters to internal
#        Send including enter
        print("on buttonsend clicked")

    def on_buttonrefresh_clicked(self, widget):
        # print("refresh clicked")
        self.service_active()
        tempstatus = self.tempstatustab.get_status()
        self.labeltemptimestamp.set_label(str(tempstatus[1]))
        if tempstatus[2] < float(self.entrymintemp1.get_text()):
            self.labelsensor1value.set_markup(t_red + str(tempstatus[2]) + t_endspan)
        elif tempstatus[2] < float(self.entrymintemp1.get_text()) + 2:
            self.labelsensor1value.set_markup(t_yellow + str(tempstatus[2]) + t_endspan)
        else:
            self.labelsensor1value.set_markup(t_black + str(tempstatus[2]) + t_endspan)
        if tempstatus[3] < float(self.entrymintemp2.get_text()):
            self.labelsensor2value.set_markup(t_red + str(tempstatus[3]) + t_endspan)
        elif tempstatus[3] < float(self.entrymintemp2.get_text()) + 2:
            self.labelsensor2value.set_markup(t_yellow + str(tempstatus[3]) + t_endspan)
        else:
            self.labelsensor2value.set_markup(t_black + str(tempstatus[3]) + t_endspan)
        if tempstatus[4] < float(self.entrymintemp3.get_text()):
            self.labelsensor3value.set_markup(t_red + str(tempstatus[4]) + t_endspan)
        elif tempstatus[4] < float(self.entrymintemp3.get_text()) + 2:
            self.labelsensor3value.set_markup(t_yellow + str(tempstatus[4]) + t_endspan)
        else:
            self.labelsensor3value.set_markup(t_black + str(tempstatus[4]) + t_endspan)
        panelstatus = self.panelstatustab.get_status()
        self.labelpaneldatetime.set_label(panelstatus[1])
        if panelstatus[3]:
            self.labelstatus.set_markup(t_red + "Alarm !!!" + t_endspan)
        elif panelstatus[2]:
            self.labelstatus.set_markup(t_yellow + "Armed" + t_endspan)
        else:
            self.labelstatus.set_markup(t_green + "Not Armed" + t_endspan)
        for labelzone in self.labelzones: 
            labelzone.set_label("")
        self.labelbattery.set_label("")
        zones = [bit for bit in (n for n in range(7)) if (panelstatus[4]) & bit]
        for zone in zones:
            if (zone == 7):
                self.labelbattery.set_markup(t_yellow + "Battery Warning" + t_endspan)
            else:
                self.labelzones[zone-1].set_markup(t_red + "Zone in alarm: " + (self._parms[12+zone]) + t_endspan)
        garagedoorstatus = self.garagedoorstatustab.get_status()
        # print ("garagedoorstatus=",garagedoorstatus)
        if (garagedoorstatus[2]):
            self.labelgaragedoor.set_label("Closed")
        else:
            self.labelgaragedoor.set_markup(t_yellow + "Opened" + t_endspan)
        self.labelgddatetime.set_label(garagedoorstatus[1])
        smokedetectorstatus = self.smokedetectorstatustab.get_status()
        if (smokedetectorstatus[2]):
            self.labelsmokedetector.set_markup(t_red + "SOUNDING" + t_endspan)
        else:
            self.labelsmokedetector.set_label("Off")

    # Support for temp log tab
    def format_temperature(self, column, cell, model, iter, columnum):
        temp = model.get_value(iter, columnum)
        if temp == -100:
            temptext = ""
        else:
            temptext = "%.1f" % temp
        cell.set_property("text",temptext)

    # Support for log tab
    def format_logcell(self, column, cell, model, iter, columnum):
##        print("cell=",columnum,model.get_value(iter, columnum))
        cell.set_property("text",model.get_value(iter, columnum))
        msglevel = model.get_value(iter, 1)
##        print("msglevel=",msglevel)
        if msglevel == 1:
            t_color = "goldenrod"
        elif msglevel == 2:
            t_color = "pink"
        else:
##            t_color = "pink"
            t_color = "white"
        cell.set_property("background",t_color)
        

    # Process signals from preferences tab
    def format_msglevel(self, celllayout, cell, model, iter, user_data):
        msglevel = model.get_value(iter, 1)
        cell.set_property("text",self.msglevels.get_value(self.msglevels.get_iter(msglevel),0))
        
    def on_buttonsave_clicked(self, widget):
        self._parms = (1,self.entrymintemp1.get_text(),self.entrymintemp2.get_text(),self.entrymintemp3.get_text(),self.entrymaxlog.get_text(),self.entrymaxtemplog.get_text(),
                        self.entrymailserver.get_text(), self.entryport.get_text(), self.entryuserid.get_text(), self.entrypassword.get_text(), self.entrytempsensor1.get_text(), 
                        self.entrytempsensor2.get_text(), self.entrytempsensor3.get_text(), self.entryzone1name.get_text(),self.entryzone2name.get_text(),
                        self.entryzone3name.get_text(), self.entryzone4name.get_text(), self.entryzone5name.get_text(), self.entryzone6name.get_text())
        self.parmstab.set_allparms(self._parms)
        msgbox("Parameters Saved")

    def on_buttonexport_clicked(self, widget):
        with open('/home/pi/zhm/data/zhmmonitorparms.bak', 'w') as myfile:
            wr = csv.writer(myfile, quoting=csv.QUOTE_NONNUMERIC) 
            wr.writerow(self._parms)
            self.parmstab.set_allparms(self._parms)
        with open('/home/pi/zhm/data/zhmmonitoreemail.bak', 'w') as myfile:
            wr = csv.writer(myfile, quoting=csv.QUOTE_NONNUMERIC) 
            for emailrow in self.emailaddressesstore:
                wr.writerow([emailrow[0],emailrow[1]]) 
        msgbox("Export of parms and email addresses complete")
        
    def on_buttonimport_clicked(self, widget):
        dialog=Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL,
                                    'Are you sure you want to import parms?')
        r=dialog.run()
        dialog.destroy()
        if r == Gtk.ResponseType.OK:
            with open('/home/pi/zhm/data/zhmmonitorparms.bak', 'r') as myfile:
                wr = csv.reader(myfile, quoting=csv.QUOTE_NONNUMERIC)
                for parmrow in wr:
                    self._parms = tuple(parmrow)
            self.parmstab.set_allparms(self._parms)
            with open('/home/pi/zhm/data/zhmmonitoreemail.bak', 'r') as myfile:
                wr = csv.reader(myfile, quoting=csv.QUOTE_NONNUMERIC)
                self.emailaddressesstore.clear()
                for emailrow in wr:
                    self.emailaddressesstore.append(emailrow)
            self.on_buttonsaveemailaddresses_clicked(widget)                
            msgbox("Import and save of parms and email addresses saved")

    def on_buttonaddemailaddress_clicked(self, widget):
        self.emailaddressesstore.append(["<New email address>",0])

    def service_active(self,killedflag=None):
        #~ print("service active clicked")
        if killedflag:
            self.conn = None
        elif self.conn:
            #~ print("testing for alive")
            try:
                self.conn.send("Alive?")
                msg = self.conn.recv()
            except:
                self.conn.close()
                self.conn = None
        else:
            #~ print("Getting address")
            address = ('localhost', 6000)
            #~ print("address",address)
            try:
                self.conn = Client(address, authkey=b'secret password')
                #~ print("self.conn=",self.conn)
            except:
                print("exception on client connect attempt - ",sys.exc_info()[0])
                self.conn = None
                
        #~ print("tconn",self.conn)
        if self.conn:
            self.buttonservice.set_label("Stop Service")
            # print ("hiding label")
            self.labelserviceerrormsg.set_label("")
            self.labelserviceerrormsg.hide()
        else:
            # print ("show LABEL")
            self.buttonservice.set_label("Start Service")
            self.labelserviceerrormsg.set_markup(t_red + "*** WARNING *** Service is not running" + t_endspan)
            self.labelserviceerrormsg.show_all()
        
    def on_buttonservice_clicked(self, widget):
        # print("buttonservice button pressed")
        self.service_active()
        if self.conn:
            print("Stopping service",self.conn)
            self.conn.send('close')
            self.conn.close()
            self.service_active(True)
        else:
            print("starting service",self.conn)
            os.system('lxterminal --working-directory=/home/pi/zhm -t "zhmservice" -e ../zhmservice &')
            self.service_active()
                
    def on_buttonsaveemailaddresses_clicked(self, widget):
        if self.emailaddressesstore:
            self.emailaddressestab.set_all(self.emailaddressesstore)
            msgbox("Email addresses saved")
        else:
            msgbox("No email addresses to save!")

    def emailaddresses_row_select(self, tree, path, column, model):
        iter = model.get_iter(path)
        d = Gtk.MessageDialog(None,
                          Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                          Gtk.MessageType.QUESTION,
                          Gtk.ButtonsType.OK_CANCEL,
                          "Edit Email Address")
        combo_msglevel=Gtk.ComboBox.new_with_model(self.msglevels)
        cell = Gtk.CellRendererText()
        combo_msglevel.pack_start(cell,True)                             
        combo_msglevel.add_attribute(cell,'text',0)
        comboentry = model.get_value(iter,1)
        combo_msglevel.set_active(comboentry)
        combo_msglevel.show()
        d.vbox.pack_end(combo_msglevel, False, False,0)
        entry = Gtk.Entry()
        entry.set_text(model.get_value(iter,0))
        entry.show()
        d.vbox.pack_end(entry,True, True,0)

        d.add_button(Gtk.STOCK_DELETE, 42)
        entry.connect('activate', lambda _: d.response(Gtk.ResponseType.OK))
        d.set_default_response(Gtk.ResponseType.OK)
        r = d.run()
        text = entry.get_text()    #.decode('utf8')
##        print ("get active", combo_msglevel.get_active())
        selected_msglevel = combo_msglevel.get_active()
        d.destroy()
        if r == Gtk.ResponseType.OK:
            model.set_value(iter,0,text)
            model.set_value(iter,1,selected_msglevel)
        elif r== 42:
            dialog=Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL,
                                    'Are you sure you want to delete this email address?')
            r=dialog.run()
            dialog.destroy()
            if r == Gtk.ResponseType.OK:
                model.remove(iter)
                
    # Network Device tab
    def netdev_row_select(self, tree, path, column, model):
        iter = model.get_iter(path)
        d = Gtk.MessageDialog(None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.OK_CANCEL,
            "Edit Device Comment")
        entry = Gtk.Entry()
        entry.set_text(model.get_value(iter,3))
        entry.show()
        d.vbox.pack_end(entry,True, True,0)

        d.add_button(Gtk.STOCK_DELETE, 42)
        entry.connect('activate', lambda _: d.response(Gtk.ResponseType.OK))
        d.set_default_response(Gtk.ResponseType.OK)
        r = d.run()
        text = entry.get_text()   
        d.destroy()
        if r == Gtk.ResponseType.OK:
            model.set_value(iter,"Comment",text)
        elif r== 42:
            dialog=Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL,
                                    'Are you sure you want to delete this entry?')
            r=dialog.run()
            dialog.destroy()
            if r == Gtk.ResponseType.OK:
                model.delete_record(iter)

    

###################################################################################################################
### start of main code

print ( 'zhomemonitor Started:', datetime.datetime.now().replace(microsecond=0), ' ',version_long)

if __name__ == "__main__":
##    os.chdir("/home/pi/zhm")
    db = sqlite3.connect("./data/zhmmonitor.db", isolation_level=None) 
    db.execute("VACUUM;")
    hwg = windowmain()
    Gtk.main()

    print ( 'zhomemonitor Ended:', datetime.datetime.now().replace(microsecond=0), ' ',version_long)
    db.close()        
