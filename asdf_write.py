#!/usr/bin/env python

"""Writes out ASDF XML files.

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
import StringIO
from lxml import etree, objectify


class ASDF(object):
    def __init__(self):
        # Set up namespaces
        nsmaps = {'xsi' : "http://www.w3.org/2001/XMLSchema-instance"}
        ns = objectify.ElementMaker(annotate=False, namespace=None, nsmap=None)
        nsxsi = objectify.ElementMaker(annotate=False, namespace=nsmaps['xsi'], nsmap=nsmaps)
        
        self.root = ns.asdf()
        self.root.attrib['version'] = '0.1'

        self.header = objectify.SubElement(self.root, "header")
        self.scene_setup = objectify.SubElement(self.root, "scene_setup")

    def Write(self, fxml):       
        etree.strip_attributes(self.root, '{http://codespeak.net/lxml/objectify/pytype}pytype')
        objectify.deannotate(self.root, xsi_nil=True)
        etree.cleanup_namespaces(self.root)
        print >>fxml, (etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding='utf-8'))

    def SetScene(self, so_list):
        for so in so_list:
            self.scene_setup.append(objectify.Element("source"))
            #if 'id' in so:
            #    self.scene_setup.source[-1].attrib['id'] = so['id']
            if 'name' in so:
                self.scene_setup.source[-1].attrib['name'] = so['name']
            if 'model' in so:
                self.scene_setup.source[-1].attrib['model'] = so['model']
            if 'file' in so:
                self.scene_setup.source[-1].file = so['file']
            if 'mute' in so:
                self.scene_setup.source[-1].attrib['mute'] = so['mute']
            if 'channel' in so:
                self.scene_setup.source[-1].file.attrib['channel'] = so['channel']
            if ('posx' in so) and ('posy' in so):
                self.scene_setup.source[-1].position = None
                self.scene_setup.source[-1].position.attrib['x'] = so['posx']
                self.scene_setup.source[-1].position.attrib['y'] = so['posy']
                self.scene_setup.source[-1].position.attrib['fixed'] = 'false'
