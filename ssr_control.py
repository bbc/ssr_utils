#!/usr/bin/env python

import socket
import time
from sys import stdout
import commands

class SSRControl():
    def __init__(self,TCP_IP,TCP_PORT):
        self.TCP_IP = TCP_IP
        self.TCP_PORT = TCP_PORT
        self.connect_socket(TCP_IP,TCP_PORT)
        self.jack_name = 'BinauralRenderer'

    def connect_socket(self,TCP_IP,TCP_PORT):
        # wait until can connect to the host and then continue
        self.ssr_loaded = False
        start_time = time.time()
        timeout = 5.#s
        while (not self.ssr_loaded):
            try:
                if ((time.time()-start_time)>timeout):
                    print "Timeout - quitting"
                    self.s.close()
                    return
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((TCP_IP, TCP_PORT))
                if not "JACK server not running" in commands.getoutput('jack_lsp'):
                    self.ssr_loaded = True
                    print("Connected to SoundScapeRenderer")
                else:
                    print "JACK not running"
                    self.s.close()
                    return
            except socket.error, msg:
                self.s.close()
                stdout.write('.')
                stdout.flush()
            time.sleep(0.5)

    def close_socket(self):
        self.s.close()

    #TRANSPORT
    def start(self):
        MESSAGE = '<request><state transport="start"/></request>' + '\0'
        self.s.send(MESSAGE)
    def stop(self):
        MESSAGE = '<request><state transport="stop"/></request>' + '\0'
        self.s.send(MESSAGE)
    def rewind(self):
        MESSAGE = '<request><state transport="rewind"/></request>' + '\0'
        self.s.send(MESSAGE)
    def seek(self,hours,mins,seconds,milliseconds=0):
        MESSAGE = '<request><state seek="' + str('%d' % hours) + ':' + str('%02d' % mins) + ':' + str('%02d' % seconds) + '.' + str('%03d' % milliseconds) + '"/></request>' + '\0'
        print MESSAGE
        self.s.send(MESSAGE)
    #SCENE
    def load_scene(self,scene_file):
        print('Loading scene: ' + scene_file + '...'),
        stdout.flush()
        MESSAGE = '<request><scene load="' + scene_file + '"/></request>' + '\0'
        self.s.send(MESSAGE)
        num_ins = 0
        num_ins_old = 1
        num_sources = self.count_sources(scene_file);
        """while num_ins < num_sources:
            time.sleep(1)
            jack_ins = commands.getoutput("jack_lsp | grep '" + self.jack_name + ":in_'")
            num_ins=jack_ins.count('\n')+int(jack_ins.__len__()>0)
            for i in range(num_ins_old,num_ins+1):
                print(i),
                stdout.flush()
            num_ins_old = num_ins+1"""
        print("Done")
        self.rewind()
    def count_sources(self,scene_file):
        num_sources = 0
        f_scene = open(scene_file, 'r')
        for line in f_scene:
            if '<source' in line:
                num_sources += 1
        f_scene.close()
        return num_sources
    def clear_scene(self):
        MESSAGE = '<request><state transport="stop"/></request>' + '\0'
        self.s.send(MESSAGE)
        MESSAGE = '<request><scene clear="true"/></request>' + '\0'
        self.s.send(MESSAGE)
    #SOURCES
    def add_source(self,name,file_path,file_channel,pos_x,pos_y,azimuth):
        MESSAGE='<request><source new="true" name="' + str(name) + '" file="' + str(file_path) + '" channel="' + str(file_channel) + '">'
        MESSAGE+='<position x="' + str(pos_x) + '" y="' + str(pos_y) + '" fixed="false"/>'
        MESSAGE+='<orientation azimuth="' + str(azimuth) + '"/></source></request>' + '\0'
        self.s.send(MESSAGE)
    def delete_source(self,source_id):
        MESSAGE='<request><delete><source id="' + str(source_id) + '"/></delete></request>' + '\0'
        self.s.send(MESSAGE)
    def mute_source(self,source_id,b_mute=True):
        mute_str = "true" if b_mute else "false"
        MESSAGE='<request><source id="' + str(source_id) + '" mute="' + mute_str + '"/></request>' + '\0'
        self.s.send(MESSAGE)
    def set_source_position(self,source_id,x,y):#in metres
        MESSAGE='<request><source id="' + str(source_id) + '"><position x="' + str(x) + '" y="' + str(y) + '"/></source></request>' + '\0'
        self.s.send(MESSAGE)
    def set_source_orientation(self,source_id,azimuth):#in degrees, zero means face +ve X axis
        MESSAGE='<request><source id="' + str(source_id) + '"><orientation azimuth="' + str(azimuth) + '"/></source></request>' + '\0'
        self.s.send(MESSAGE)
    def set_source_volume(self,source_id,volume):#in dB
        MESSAGE='<request><source id="' + str(source_id) + '" volume="' + str(volume) + '"/></request>' + '\0'
        self.s.send(MESSAGE)
    def move_source_position(self,source_id,x_start,y_start,x_end,y_end,duration,interval=0.001):
        start_time = time.time()
        next_message_time = start_time + interval
        # linearly interpolate between points
        num_steps=round(duration/interval)
        x_step = (x_end-x_start)/num_steps
        y_step = (y_end-y_start)/num_steps
        x_cur = x_start
        y_cur = y_start
        for ix in range(0,int(num_steps)):
            message_start_time = time.time()
            next_message_time += interval

            x_cur+=x_step
            y_cur+=y_step
            self.set_source_position(source_id,x_cur,y_cur)
            
            message_finish_time=time.time()
            if (next_message_time>message_finish_time):
                sleep(next_message_time-time.time())
            else:
                print "overrun"
        total_time=message_finish_time-start_time
        #print "Time actually taken:" + str(total_time)
    def move_source_volume(self,source_id,vol_start,vol_end,duration,interval=0.001):
        start_time = time.time()
        next_message_time = start_time + interval
        # linearly interpolate between points
        num_steps=round(duration/interval)
        vol_step = (vol_end-vol_start)/num_steps
        vol_cur = vol_start
        for ix in range(0,int(num_steps)):
            message_start_time = time()
            next_message_time += interval
            
            vol_cur+=vol_step
            self.set_source_volume(source_id,vol_cur)

            message_finish_time=time()
            if (next_message_time>message_finish_time):
                sleep(next_message_time-time())
            else:
                print "overrun"
        total_time=message_finish_time-start_time
        #print "Time actually taken:" + str(total_time)  
