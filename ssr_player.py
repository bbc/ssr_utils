#!/usr/bin/env python

"""The SSR player executable.

Copyright 2014 British Broadcasting Corporation.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""

import sys
import wave_bwf
from math import *
from adm_read_xml import *
import ssr_control
import time
from subprocess import Popen, PIPE
from adm2asdf import *
from adm_parser import *
import argparse

###########################
# Class: SSRPlayer
# This allows playback of object-based audio with the SoundScape Renderer
###########################
class SSRPlayer(object):
    def __init__(self, _pos_grid, _port=4711, renderer="binaural", config=None, ssr_args=None):
        sys.stdout.write("SSRPlayer: initialising")
        self.PORT = _port
        self.pos_grid = _pos_grid
        commands = ['ssr-' + renderer]
        commands.append('--input-prefix=DUMMY') # prevent inputs being connected to system capture
        commands.append('--ip-server='+str(self.PORT))
        if config:
            commands.append('--config='+config)
        if ssr_args:
            for ssr_arg in ssr_args:
                commands.append(ssr_arg)
        
        self.ssr_process = Popen(commands)
        # let things settle
        for i in range(0, 5):
            time.sleep(0.5) 
            sys.stdout.write(".")
        sys.stdout.write("SSRPlayer: initalised\n")

    def Setup(self, fname):
        sys.stdout.write("SSRPlayer: beginning setup\n")
        self.ssr = ssr_control.SSRControl('localhost', self.PORT)
        pos = self.pos_grid[0]
        self.id_table = []
        for i, pos_list in enumerate(pos['pos']):
            self.id_table.append(i + 1)
            model = 'point'
            if pos_list['diffuse']:
                model = 'plane'
            self.ssr.add_source(pos_list['name'], fname, pos_list['tr'], pos_list['posx'], pos_list['posy'], None, model)
        # give time for sources appear
        for i in range(0, 4):
            time.sleep(0.5)
            sys.stdout.write(".")
        sys.stdout.write("\nSSRPlayer: setup complete\n")

    def Play(self):
        sys.stdout.write("SSRPlayer: playing\n")
        self.ssr.start()
        start_time = time.time()
        co = 0
        lstart = 0.0
        for pos in self.pos_grid:
            if co > 0:
                lpos = self.pos_grid[co - 1]                
                done = False
                while not done:
                    now = (time.time() - start_time)
                    if now < pos['start'] and now >= lstart:
                        for i, pos_list in enumerate(pos['pos']):
                            lpos_list = lpos['pos'][i]
                            so_id = '%d' % (self.id_table[i])
                            if pos_list['ok']:
                                self.ssr.mute_source(so_id, False)
                            else:
                                self.ssr.mute_source(so_id, True)
                            self.ssr.set_source_position(so_id, pos_list['posx'], pos_list['posy'])
                        done = True
            lstart = pos['start']
            co += 1
        time.sleep(1.0)
        self.ssr.stop()

    def Finish(self):
        sys.stdout.write("SSRPlayer: stopping\n")
        self.ssr_process.terminate()
     


################
# MAIN
################

def main():

    parser = argparse.ArgumentParser(description='Play a BWF file using the SoundScape Renderer. (Unknown arguments are forwarded to the SoundScape Renderer.)')
    parser.add_argument('bwf_file', metavar='<bwf input file>.wav', nargs=1,
                   help='BWF WAV file to be played')
    parser.add_argument('--renderer', default="binaural",
                   help='SSR renderer type')
    parser.add_argument('--ip_port', type=int, default=4711,
                   help='IP port for socket communication with SSR. (Default=4711)')
    parser.add_argument('--ssr-config', metavar='CONFIG_FILE',
                   help='SoundScape Renderer configuration file')
    
    args,unknown_args = parser.parse_known_args()
    
    # Open BWF wav file
    tracklist, fxml, file_duration = ExtractBWF(args.bwf_file[0])

    # Parse ADM XML to get object and track info
    obj_uid, track_actions = parseXML(fxml, tracklist)

    # Generate a list of objects
    objpos_list, tr_list, num_tr = ObjectList(obj_uid, track_actions)

    # Rearrange objects into a time v. channel array of metadata
    pos_grid = TimePositionGrid(objpos_list, tr_list, 0.1, file_duration)

    # Setup and run SSR player
    player = SSRPlayer(pos_grid, _port=args.ip_port, renderer=args.renderer, config=args.ssr_config, ssr_args=unknown_args)
    player.Setup(args.bwf_file[0])
    player.Play()
    player.Finish()


# Extracts bext, chna and axml chunk info from BWF file
def ExtractBWF(fname):
    # Open BWF wav file
    f = wave_bwf.open(fname, 'r')
    params = f.getparams()
    file_duration = float(params[3]) / float(params[2])
    print "Duration: %3.2fs" % (file_duration)

    # Read bext chunk
    f.read_bext()

    # Get track list from chna chunk
    tracklist = ConvertChna(f)
    if not tracklist:
        print "Can't read CHNA"
        return 0
 
    # Read XML from axml chunk
    fxml = StringIO.StringIO()
    fa = f.read_axml()
    fxml.write(fa)
    fxml.seek(0)
    return tracklist, fxml, file_duration  



if __name__ == '__main__':
    main()

