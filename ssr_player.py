#!/usr/bin/env python

import sys
import wave_bwf
from math import *
from adm_read_xml import *
import ssr_control
import time
from subprocess import Popen, PIPE
from adm2asdf import *
from adm_parser import *


class SSRPlayer(object):
    def __init__(self, _pos_grid, _port=4711, hrir_file=None, hrir_size=None, loop=False):
        sys.stdout.write("SSR Player...")
        self.PORT = _port
        self.pos_grid = _pos_grid
        commands = ['ssr-binaural']
        if hrir_file:
            commands.append('--hrirs='+hrir_file)
        if hrir_size:
            commands.append('--hrir-size='+str(hrir_size))
        if loop:
            commands.append('--loop')
        commands.append('--input-prefix=DUMMY')
        commands.append('--ip-server='+str(self.PORT))
        commands.append('--threads=2')
        self.ssr_process = Popen(commands, stdout=PIPE, stderr=PIPE)
        # let things settle
        for i in range(0, 5):
            time.sleep(0.5) 
            sys.stdout.write(".")
        sys.stdout.write("initalised\n")

    def Setup(self, fname):
        sys.stdout.write("SSR Player...")
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
        sys.stdout.write("setup complete\n")

    def Play(self):
        sys.stdout.write("SSR Player...playing")
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
        sys.stdout.write("SSR Player...stopping")

        self.ssr_process.communicate()
        self.ssr_process.terminate()
     


################
# MAIN
################

def main():
    args = sys.argv[1:]
    if len(args) < 2 or len(args) > 3:
        Usage()

    # Read in some command line stuff
    hrir_file = None
    hrir_size = None    
    if args[1] != '-':
        hrir_file = args[1]
        hrir_size = 65536
    loop = False
    if len(args) == 3:
        if args[2] == '-loop':
            loop = True
            print "Looping" 

    # Open BWF wav file
    tracklist, fxml, file_duration = ExtractBWF(args[0])

    # Parse ADM XML to get object and track info
    obj_uid, track_actions = parseXML(fxml, tracklist)

    # Generate a list of objects
    objpos_list, tr_list, num_tr = ObjectList(obj_uid, track_actions)

    # Rearrange objects into a time v. channel array of metadata
    pos_grid = TimePositionGrid(objpos_list, tr_list, 0.1, file_duration)

    # Setup and run SSR player
    player = SSRPlayer(pos_grid, hrir_file=hrir_file, hrir_size=hrir_size, loop=loop)
    player.Setup(args[0])
    player.Play()
    while loop:
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


# Command line usage
def Usage():
    print >>sys.stderr, "python ssr_player.py <wav input file> <hrir file> [-loop]"
    print >>sys.stderr, "     Use '-' for hrir file if one isn't being used."
    sys.exit(0)    



if __name__ == '__main__':
    main()

