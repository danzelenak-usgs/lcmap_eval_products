#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Dan Zelenak

Last Updated: 8/7/2017

Usage: Calculate the number of changes per pixel across all available
CoverMap layers.  Alternatively can specify a 'from' and 'to' and the script
will calculate the number of changes for each year interval within
the given range.

"""
import datetime
import glob
import os
import subprocess
import sys
from shutil import copy2

import numpy as np

try:
    from osgeo import gdal
    # from osgeo.gdalconst import *
except ImportError:
    import gdal

print(sys.version)

t1 = datetime.datetime.now()
print("\nProcessing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n"))

gdal.AllRegister()
gdal.UseExceptions()


def get_inlayers(infolder, name, y1, y2):
    """
    
    Generate a list of the input Cover Map layers with full paths

    Args:
        infolder: <string> the directory containing the annual cover map layers
        y1: <string> the 'from' year
        y2: <string> the 'to' year

    Returns:
        templist: <list> contains strings of full paths to all cover map layers
        - or -
        flist: <list> contains strings of full paths to cover map layers in
                range of y1 and y2
    
    """

    templist = glob.glob("{}{}*{}*.tif".format(infolder, os.sep, name))

    templist.sort()

    if y1 is None or y2 is None:

        return templist

    else:

        ylist = [y for y in range(int(y1), int(y2) + 1)]

        flist = [r for y in ylist for r in templist if str(y) in r]

        return flist


def get_outlayers(inrasters, outfolder, name):
    """
    
    Generate a list of output rasters containing full paths

    Args:
        inrasters: <list> list of the input rasters containing full paths
        outfolder: <string> the full path to the output folder
        name: <string> the name of the cover product

    Return:
        outlist: <list> list of full paths to output rasters
        years: <list> list of years as strings
    
    """

    years = []

    for r in range(len(inrasters)):

        base = os.path.splitext(os.path.basename(inrasters[r]))[0]

        pieces = base.split("_")

        for piece in pieces:

            if len(piece) == 4:

                try:
                    int(piece)

                    years.append(piece)

                except ValueError:
                    continue

        # years.append(fname[-4:])

    outlist = ["{}{}{}{}to{}ct.tif".format(outfolder, os.sep, name, years[0], years[i]) for i in range(len(inrasters))]

    return outlist, years


def do_calc(in_files, out_r):
    """
    
    Generate the output layers and add color ramps for the default
    from/to years (i.e. the min and max years present)

    Args:
        in_files: <list> contains strings representing full paths to input rasters
        out_r: <string> the full path of the output raster file

    Returns:
        None
    
    """

    driver = gdal.GetDriverByName("GTiff")

    src0 = gdal.Open(in_files[0])

    rows = src0.RasterYSize
    cols = src0.RasterXSize

    srcdata0 = src0.GetRasterBand(1).ReadAsArray()

    # Create a copy of the first cover map to contain "holder" values
    # which will be used to compare future values to determine
    # whether a change has occurred.  Each element's value will be updated
    # each time that a valid class change occurs.
    holder = np.copy(srcdata0)

    # an array of zeros that will contain the summed number of changes
    # per pixel
    sum_change = np.zeros_like(holder, dtype=np.int8)

    for index, infile in enumerate(in_files):

        tempmask = np.zeros_like(holder, dtype=np.int8)

        # skip the first file in the input files list
        if index == 0:

            continue

        # The current cover map being tested
        tempsrc = gdal.Open(infile, gdal.GA_ReadOnly)

        # The current cover map converted to a numpy array
        tempdata = tempsrc.GetRasterBand(1).ReadAsArray()

        if index == 1:
            # For the first year after year 0, we don't want to include
            # class 9 in year 0 changing to any other class as a 
            # countable change, so replace it with the value that exists in 
            # the following year.
            holder[holder == 9] = tempdata[holder == 9]

            # Do the same for any "insufficient data" class 0 instances
            holder[holder == 0] = tempdata[holder == 0]

        # recode class 9 to previous non-9 class value (i.e. no change)
        tempdata[tempdata == 9] = holder[tempdata == 9]

        # do the same for class 0
        tempdata[tempdata == 0] = holder[tempdata == 0]

        # any classes in current year that don't equal the class in holder
        # are flagged as change with value of 1
        tempmask[tempdata != holder] = 1

        # update holder elements with most recent changed classes
        holder[tempdata != holder] = tempdata[tempdata != holder]

        # sum the current number of changes
        sum_change = sum_change + tempmask

        # reset these temporary datasources to None
        tempsrc, tempdata = None, None

    outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_Byte)

    if outfile is None:
        print("\nCould not create image file {a}".format
              (a=os.path.basename(out_r)))

        sys.exit(1)

    outband = outfile.GetRasterBand(1)
    outband.WriteArray(sum_change, 0, 0)

    outband.FlushCache()
    # outband.SetNoDataValue(255)

    outfile.SetGeoTransform(src0.GetGeoTransform())
    outfile.SetProjection(src0.GetProjection())

    src0, outfile = None, None

    return None


def add_color_table(in_vrt, clr_table, dtype):
    """
    
    Write color map info to a VRT file

    Args:
        in_vrt: <string> path to the input VRT file
        clr_table: <string> path to the input color table (.txt)
        dtype: <string> the bit depth of the original raster
    
    Return:
        out_vrt: <string> path to the VRT with color map info written to it
    
    """

    color_table = open(clr_table, "r")

    (dirName, fileName) = os.path.split(in_vrt)
    (fileBase, fileExt) = os.path.splitext(fileName)

    out_vrt = r"{0}{1}zzzzz{2}_temp.vrt".format(dirName, os.sep, fileBase)

    in_txt = open(in_vrt, 'r+')
    out_txt = open(out_vrt, 'w')

    with open(in_vrt, 'r+') as in_txt, open(out_vrt, "w") as out_txt:

        # key is the line after which to insert the color table in the VRT
        key = '<VRTRasterBand dataType="{0}" band="1">'.format(dtype)

        # subkey is a line that doesn't need to be in the new VRT text
        subkey = "   <ColorInterp>Gray</ColorInterp>"

        # get lines in a list
        txt_read = in_txt.readlines()

        for line in txt_read:

            if subkey in line:

                continue

            else:

                writetxt = r"{0}".format(line)

                out_txt.write(writetxt)

                # insert color table following keywords
                if key in line:

                    # print "\nFound the key!\n"
                    color_read = color_table.readlines()

                    # print 'writing color table to vrt'
                    for ln in color_read:
                        out_txt.write(ln)

    return out_vrt


def add_color(outdir, raster):
    """
    
    Add a color map to the created raster files

    Args:
        outdir: <string> path to the output folder
        raster: <string> path to the current raster being worked on

    Return:
        None
    
    """

    namex = os.path.basename(raster)
    name = os.path.splitext(namex)[0]

    if not os.path.exists(outdir + os.sep + "color"):
        os.mkdir(outdir + os.sep + "color")

    outfile = outdir + os.sep + "color" + os.sep + namex

    clr_table = "Color_tables{}color_numchanges.txt".format(os.sep)

    outcsv_file = r'%s%szzzzzz_%s_list.csv' % (outdir, os.sep, name)

    if os.path.isfile(outcsv_file):
        os.remove(outcsv_file)

    with open(outcsv_file, 'w') as outcsv2_file:

        outcsv2_file.write(str(raster) + "\r\n")

    temp_vrt = '{}{}zzzz_{}.vrt'.format(outdir, os.sep, name)
    com = 'gdalbuildvrt -q -input_file_list %s %s' % (outcsv_file, temp_vrt)
    subprocess.call(com, shell=True)

    out_vrt = add_color_table(temp_vrt, clr_table, 'Byte')

    runCom = "gdal_translate -of GTiff -ot Byte -q %s %s" % (out_vrt, outfile)
    subprocess.call(runCom, shell=True)

    # remove the temp files used for adding the color tables
    for v in glob.glob(outdir + os.sep + "zzz*"):
        os.remove(v)

    return None


def clean_up(outdir):
    """
    
    Remove duplicate files in the output directory, move the
    rasters with colortable added from /color to the main output directory.

    Args:
        outdir: <string> the full path to the output directory

    Return:
        None
    
    """
    # remove the original uncolored rasters first
    rlist = glob.glob(outdir + os.sep + "*.tif")

    for r in rlist: os.remove(r)

    # copy the colored rasters to the main output directory
    nlist = glob.glob(outdir + os.sep + "color" + os.sep + "*.tif")

    for n in nlist: copy2(n, outdir)

    # remove the old copies of the colored rasters
    for n in nlist: os.remove(n)

    # remove the /color directory
    os.removedirs(outdir + os.sep + "color")

    return None


def usage():
    print("\t[-i Full path to the directory where annual CCDC "
          "cover map layers are saved]\n"
          "\t[-from The start year]\n"
          "\t[-to The end year]\n"
          "\t[-name the cover map product name]\n"
          "\t**CoverPrim or CoverSec are valid names**\n"
          "\t[-o Full path to the output folder]\n"
          "\n\t*Output raster will be saved in the same format "
          "as input raster (GTiff).\n\n"

          "\tExample: 5_ccdc_cover_changes.py -i /.../ChangeMaps -from 1984 -to 2015"
          " -o /.../OutputFolder -name CoverPrim")

    return None


def main():
    fromY, toY = None, None

    argv = sys.argv

    if len(argv) < 3:
        print("\n\tMissing one or more arguments:\n ")

        usage()

        sys.exit(1)

    # Parse command line arguments.
    i = 1
    while i < len(argv):

        arg = argv[i]

        if arg == '-i':
            i = i + 1
            inputdir = argv[i]

        elif arg == '-from':
            i = i + 1
            fromY = argv[i]

        elif arg == '-to':
            i = i + 1
            toY = argv[i]

        elif arg == '-o':
            i = i + 1
            outputdir = argv[i]

        elif arg == '-name':
            i = i + 1
            name = argv[i]

        elif arg == '-help':
            usage()
            sys.exit(1)

        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)

        i += 1

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    if fromY is None: fromY = "1984"

    if toY is None: toY = "2015"

    # create a new subdirectory based on the "from" and "to" years
    # to keep accumulated sets organized
    outputdir = outputdir + os.sep + "{a}_{b}".format(a=fromY, b=toY)

    if not os.path.exists(outputdir): os.makedirs(outputdir)

    infiles = get_inlayers(inputdir, name, fromY, toY)

    print("Input Files are:\n".format(infiles))

    outfiles, years = get_outlayers(infiles, outputdir, name)

    # for x in range(len(outfiles)):
    for index, outfile in enumerate(outfiles):

        if index == 0:
            continue

        if not os.path.exists(outfile):
            print("\nGenerating raster file {} from years: ".format(os.path.basename(outfile)))

            print(years[0], " and ", years[index])

            do_calc(infiles[0:index + 1], outfile)

        add_color(outputdir, outfile)

    clean_up(outputdir)

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()
print("\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1
print("Processing time: " + str(tt), "\n")
