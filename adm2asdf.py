#!/usr/bin/env python

import sys
from math import *
from asdf_write import *
from adm_parser import *

# Bodge for distance scaling
abs_dis = 3.0

# Go through each object and extract channel & block metadata for renderer
def ObjectList(obj_uid, track_actions):
    num_tr = 0
    tr_list = []
    objpos_list = []
    for obj in obj_uid:
        objpos_ch_list = []
        for uid in obj['uids']:
            for track in track_actions:
                # Only does it for 'DirectSpeakers' and 'Objects' type of channel (type 1 and 3).
                if track[1] == uid and (track[2]['type'] == 1 or track[2]['type'] == 3):
                    objpos_ch = {}
                    if not (track[0] in tr_list):
                        tr_list.append(track[0])
                        num_tr = 0 
                    objpos_ch['channel'] = track[0]
                    objpos_ch['blocks'] = []
                    for block in track[2]['blocks']:
                        blockpos = {}
                        blockpos['start'] = block.GetStart()
                        blockpos['duration'] = block.GetDuration()
                        blockpos['posx'] = CalcPosX(block.GetPosition())
                        blockpos['posy'] = CalcPosY(block.GetPosition())
                        blockpos['diffuse'] = block.GetDiffuse()
                        objpos_ch['blocks'].append(blockpos)         
                    objpos_ch_list.append(objpos_ch)
        objpos_list.append({'id': obj['id'], 'name': obj['name'], 'objs': objpos_ch_list})
    return objpos_list, tr_list, num_tr


# Convert object based info into a time-frame based array of values
def TimePositionGrid(objpos_list, tr_list, step, file_duration):
    tc = 0.0
    fsize = step
    pos_grid = []
    while (True):
        pos_list = []
        none_ok = True
        for tr in tr_list:
            posx = 0.0
            posy = abs_dis
            ok = False
            oid = None
            oname = None
            diffuse = False
            for objpos in objpos_list:
                for objs in objpos['objs']:
                    if objs['channel'] == tr:
                        oid = objpos['id']
                        oname = objpos['name']
                        for block in objs['blocks']:
                            if block['start'] and block['duration']:
                                if TimeConv(block['start']) <= tc and (TimeConv(block['start']) + TimeConv(block['duration'])) > tc:
                                    posx = block['posx']
                                    posy = block['posy']
                                    diffuse = block['diffuse']
                                    ok = True
                            else:
                                posx = block['posx']
                                posy = block['posy']
                                diffuse = block['diffuse']
                                ok = True                                
            pos_list.append({'id': oid, 'name': oname, 'tr': tr, 'ok': ok, 'posx': posx, 'posy': posy, 'diffuse': diffuse})
            if ok:
                none_ok = False
        pos_grid.append({'start': tc, 'pos': pos_list})
        tc += fsize
        if tc > file_duration:
            break
        #if none_ok:
        #    break
    return pos_grid


# Write out an ASDF file for each time instant
def WriteASDFFiles(pos_grid, wavname, asdfname):
    for pos in pos_grid:
        ind = '%05d' % (int(pos['start'] * 10.0))
        fout = open(asdfname + '_' + ind + '.asd', 'w')
        asdf = ASDF()
        fname = wavname
        so_list = []
        for pos_list in pos['pos']:
            so_dic = {}
            if pos_list['diffuse']:
                so_dic['model'] = 'plane'
            else:
                so_dic['model'] = 'point'
            so_dic['id'] = '%d' % (pos_list['tr'])
            so_dic['name'] = pos_list['name']
            so_dic['file'] = fname
            if pos_list['ok']:
                so_dic['mute'] = 'false'
            else:
                so_dic['mute'] = 'true'
            so_dic['channel'] = '%d' % (pos_list['tr'])
            so_dic['posx'] = '%3.3f' % (pos_list['posx'])
            so_dic['posy'] = '%3.3f' % (pos_list['posy'])
            so_list.append(so_dic)

        asdf.SetScene(so_list)
        asdf.Write(fout)
        fout.close()


# Write out the ASDF for the first time instant
def WriteFirstASDFFile(pos_grid, wavname, asdfname):
    pos = pos_grid[0]
    fout = open(asdfname + '_first.asd', 'w')
    asdf = ASDF()
    fname = wavname
    so_list = []
    for pos_list in pos['pos']:
        so_dic = {}
        so_dic['model'] = 'point'
        so_dic['id'] = '%d' % (pos_list['tr'])
        so_dic['name'] = pos_list['name']
        so_dic['file'] = fname
        if pos_list['ok']:
            so_dic['mute'] = 'false'
        else:
            so_dic['mute'] = 'true'
        so_dic['channel'] = '%d' % (pos_list['tr'])
        so_dic['posx'] = '%3.3f' % (pos_list['posx'])
        so_dic['posy'] = '%3.3f' % (pos_list['posy'])
        so_list.append(so_dic)

    asdf.SetScene(so_list)
    asdf.Write(fout)
    fout.close()
    return asdfname + '_first.asd'

# Calc X value from spherical coords
def CalcPosX(pos):
    d = pos['distance']['max'] * abs_dis
    az = pos['azimuth']['max'] * pi / 180.0
    el = (pi / 2.0) - (pos['elevation']['max'] * pi / 180.0)
    x = d * sin(el) * sin(az)
    return x

# Calc Y value from spherical coords
def CalcPosY(pos):
    d = pos['distance']['max'] * abs_dis
    az = pos['azimuth']['max'] * pi / 180.0
    el = (pi / 2.0) - (pos['elevation']['max'] * pi / 180.0)
    y = d * sin(el) * cos(az)
    return y

# Calc Z value from spherical coords
def CalcPosZ(pos):
    d = pos['distance']['max'] * abs_dis
    az = pos['azimuth']['max'] * pi / 180.0
    el = (pi / 2.0) - (pos['elevation']['max'] * pi / 180.0)
    z = d * cos(el)
    return z

# Convert time string to a float
def TimeConv(ts):
    hr = int(ts[0:2])
    mn = int(ts[3:5])
    sec = int(ts[6:8])
    msec = int(ts[9:15])
    tsec = (float(hr) * 3600.0) + (float(mn) * 60.0) + float(sec) + (float(msec) * 0.00001)
    return tsec



