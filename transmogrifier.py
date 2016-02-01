#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'mark'

import lxml.etree as ET
import fnmatch
import os
import os.path


import sys

# dir ="/home/mark/Briefcase/Storage/ODK Briefcase Storage/forms/PSEIA_Lattice 2015-1.13/instances"
# dir ="/home/mark/Briefcase/Storage/ODK Briefcase Storage/forms"
# dir ="C:\\RBI-Data\\Briefcase\\ODK Briefcase Storage\\forms\\PSEIA_Lattice 2015-1.13\\instances"
# dir ="C:\\RBI-Data\\Briefcase\\ODK Briefcase Storage\\forms\\PSEIA_Monopole_2015-1.15\\instances"
dir ="C:\\RBI-Data\\Briefcase\\ODK Briefcase Storage\\forms"


# List of tags that require the removal of a string
removal_list=[["manufacturer","manufacturer_"],["external_coating_colour","external_colour_"]]

# List of tags that require the removal of underscores
us_list = ["inspector_name", "manufacturer", "ground_conditions", "infrastructure_contractor","road_conditions",
           "ease_of_access","external_coating_colour"]

# List of tags that require conversion to Title case
title_list = ["site_name"]

# List of tags that require conversion to standalone GPS tags
loc_list = ["gps_location"]

# List of tags that require conversion or 0,1 to Yes, No
yes_list = ["first_time", "sign_board", "fall_arrest_section_exists","operationally_active",
            "redundant_equipment_present","mid_man_way_door_exists","stub_section_exists","gusset_base_section_exists",
            "gusset_spine_section_exists","gusset_collar_section_exists","shaft_stiffener_fitted","shaft_spine_exists",
            "cable_window_used","cable_gantry_outside",""]

namespace_string = "{http://opendatakit.org/submissions}"

def show_conversion(tag, text, converted_text):
    print tag, text, "->", converted_text

def dec2dms(dec_loc, dir):
    deg = int(dec_loc)
    dec_min = (dec_loc - deg) * 60
    min = int(dec_min)
    sec = (dec_min - min) * 60
    z= round(sec, 2)
    d_sym = " "
    s_string =  str(abs(deg)) + d_sym + str(abs(min)) + "' " + str(abs(z)) + '"'
    if deg >= 0:
        if dir == "lat":
            s_string += " N"
        else:
            s_string += " E"
    else:
        if dir == "lat":
            s_string += " S"
        else:
            s_string += " W"
    # print (s_string)
    return s_string

def decdeg2dms(dd):
   is_positive = dd >= 0
   dd = abs(dd)
   minutes,seconds = divmod(dd*3600,60)
   degrees,minutes = divmod(minutes,60)
   degrees = degrees if is_positive else -degrees
   return (degrees,minutes,seconds)

def insert_node(node, tag, value=""):
    child = ET.Element(tag)
    if not value == "":
        child.text = str(value)
        node.insert(0,child)
    else:
        node.append(child)

# modification
def modify(doc):
    retval = ""
    for el in doc.xpath("//*"):                 # process all elements
        text = el.text                          # get the text part of the element
        tag = el.tag                            # get the tag part of the element

        if text:

            clean_tag = tag.partition("}")      # partition function returns a tuple
            tag = clean_tag[2]

            # replace one string with another section
            for rw_tag in removal_list:
                if rw_tag[0] == tag:
                    clean_text = text.replace(rw_tag[1],"")
                    el.text = clean_text
                    show_conversion(tag, text, clean_text)
                    text = clean_text

            # replace underscore sectin
            for us_tag in us_list:
                if us_tag == tag:
                    clean_text = text.replace("_", " ")
                    el.text = clean_text
                    show_conversion(tag, text, clean_text)
                    text = clean_text

            # Convert to Title case section
            for title_tag in title_list:
                if title_tag == tag:
                    clean_text = text.title()
                    el.text = clean_text
                    show_conversion(tag, text, clean_text)
                    text = clean_text

            # Convert 1,0 to Yes,No alternatives
            for yes_tag in yes_list:
                if yes_tag == tag:
                    if text == "1":
                        clean_text = "Yes"
                    else:
                        clean_text = "No"
                    el.text = clean_text
                    show_conversion(tag, text, clean_text)
                    text = clean_text

            # Create proper DMS versions of location strings
            for loc_tag in loc_list:
                if loc_tag == tag:
                    location = text.split(" ")
                    print location
                    lat_dec = float(location[0])
                    lon_dec = float(location[1])
                    alt = float(location[2])
                    accuracy = float(location[3])
                    lat_str = dec2dms(lat_dec, "lat")
                    lon_str = dec2dms(lon_dec, "lon")
                    clean_text = lat_str + " :: " + lon_str
                    el.text = clean_text
                    insert_node(el, "gps_accuracy", str(accuracy))
                    insert_node(el, "gps_altitude", str(alt))
                    insert_node(el, "gps_longitude", lon_str)
                    insert_node(el, "gps_latitude", lat_str)

                    show_conversion(tag, text, clean_text)
                    text = clean_text

            if tag == "instanceID":
                print tag
                print text
                retval = text

    return retval


class L:
    def __init__(self,loading):
        # unpack data from XML node
        height = loading.find(ns("loading_height")).text
        size = loading.find(ns("loading_size")).text
        type = loading.find(ns("loading_make")).text
        pole_mount = loading.find(ns("loading_pole_mount")).text
        el_tilt = loading.find(ns("loading_electrical_tilt")).text
        mech_tilt = loading.find(ns("loading_mechanical_tilt")).text
        azim = loading.find(ns("loading_azimuth")).text

        # Do any sanitizing needed
        if not isinstance(height, str) :
            height = "0"

        # allocated data to object variables
        self.height = height
        self.owner = loading.find(ns("loading_owner")).text
        self.make = loading.find(ns("loading_make")).text
        self.size = size
        self.type = type
        self.pole_mount = pole_mount
        self.el_tilt = el_tilt
        self.mech_tilt = mech_tilt
        self.azim = azim

    def makeNode(self, newNode):
        members = vars(self)
        for member in members:
            newNodeName = ET.Element(member)
            newNodeName.text = getattr(self, member)
            newNode.append(newNodeName)


    def __cmp__(self,other):
        return cmp(self.count,other.count)

# This helper function just prepends the Namespace string to a tag so that it will work in searches properly
def ns(tag):
    return namespace_string + tag


def create_loading_table(doc):
    print "processing loading table now"
    root = doc.getroot()
    # print root.tag, root.attrib

    # for child in root:
    #     if("loadings_group" in child.tag):
    #         print child.tag, child.attrib

    group = root.find(ns("loadings_group"))
    if group is None:
        print "Damn - no loadings group found"
    elif len(group) > 0:
        print "... found a loading group"
        loading_list = []
        loading_count = 0
        for loading_node in group.findall(ns("loading_repeat")):
            loading_count += 1
            new_loading = L(loading_node)
            loading_list.append(new_loading)

        print "Found " + str(loading_count) + " loadings"
        insert_node(group, "loadings_present", str(loading_count))

        sorted_loading_list = sorted(loading_list, key = lambda l: int(l.height))
        print "Now sorted"

        # output loading table back into XML document in memory
        ltNode = ET.Element("loading_table")

        for loading in sorted_loading_list:
            newNodeStr = "LT-repeat"
            newNode = ET.Element(newNodeStr)
            loading.makeNode(newNode)
            print loading.height
            ltNode.append(newNode)

        group.insert(0, ltNode)

    else:
        print "....no loadings on this tower"
        # insert_node(root, "loadings_group", "Added"  )
        insert_node(group, "loadings_present", "0")


#
# The transmogrifier searches for specific patterns in submission.xml files and replaces them with a designated
# replacement pattern
#
if len(sys.argv) <= 1:
    print "Usage : python transmogrifier.py <input filename> <output filename>"
else:
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    matches = []
    uuid_paths = []
    sites = []
    count = 0
    if os.path.exists(dir):
        for root, dirnames, filenames in os.walk(dir):
            # print root
            # print dirnames
            # print filenames
            for filename in fnmatch.filter(filenames, '*.xml'):
                matches.append(os.path.join(root, filename))
                uuid_paths.append(root)
                count += 1
    else:
        print dir , " does not exist"

    print "Examined ", count, " files"
    print "Found " , len(matches), " .xml files to search"

    for file_name in matches:

        input_filename = file_name          # actually dealing with full paths here
        dir, infilename = os.path.split( file_name)

        if not "uuid" in dir:
            print "Skipping processing for non-UUID directory " + dir
        else:
            file, ext = os.path.splitext(infilename)

            output_dir = dir + "/mog/"
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)

            output_filename =  output_dir + file + ".mog"

            print "Input " + input_filename

            # input
            doc = ET.parse(input_filename)

            # modification of data in place
            uuid = modify(doc)

            create_loading_table(doc)

            if uuid:
                clean_uuid = uuid.replace(":", "")
                print clean_uuid

            root_path = uuid_paths[matches.index(file_name)]
            print root_path
            print "Output " + output_filename

            # output
            open(output_filename, 'w').write(ET.tostring(doc, pretty_print=True))

