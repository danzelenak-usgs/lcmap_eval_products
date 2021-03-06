"""
Created on Mon Apr 17 11:29:56 2017
Last updated on Tue Apr 25, 2017
Author: Daniel Zelenak
daniel.zelenak.ctr@usgs.gov

1.  Open a targeted raster file (should be thematic)
2.  Convert to a numpy array
3.  Mask the array based on a user-defined class value
4.  Write the masked array to a new temporary raster file
5.  Polygonize and delete the temporary raster file
6.  Iterate through steps 2-5 for each class value

Useage: Take an input thematic raster layer and a list of pixel class values to create a polygon shapefile for each
class.

***Note: Classes with larger quantities may take a long time to process***
"""

import datetime
import os
import sys
import argparse

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

gdal.UseExceptions()
gdal.AllRegister()


def get_time():
    """
    Return the current time
    :return:
    """
    return datetime.datetime.now()


def get_class_values(x):
    """TODO: Takes in a user-specified class value which will be used to
    create a new shapefile from matching pixel values.

    Args:
        x = list of the concatenated classes to search the raster layer for
       (e.g. 608 == CCD Class 06 and Trends/NLCD Class 08)

    Returns:
        x = a formated value of the concatenated classes
     """

    x = x.split(",")

    for i in range(len(x)):
        x[i] = int(x[i])

    return x


def get_outname(indir, outdir, xclass):
    """Generate output file names based on the input raster name

    Args:
        indir = full path to the input raster
        outdir = the full path to the output folder
        xclass = the target class value

    Returns:
        outdir = full path to the output location
    """

    inpath, infile = os.path.split(indir)
    fname, ext = os.path.splitext(infile)

    outname = "{a}_{b}".format(a=fname, b=str(xclass))

    outdir = outdir.replace("\\", "/")

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    output = outdir + "/" + outname

    return output


def get_array(ds):
    """Read in the raster data source and write the data to a numpy array

    Args:
        ds = full path to the raster file

    Returns:
        src_array = numpy array object generated from the raster data
    """

    # replace windows ' \ ' with the friendlier ' / '
    ds.replace('\\', '/')

    src_ds = gdal.Open(ds)

    if src_ds is None:
        print('Unable to open {}'.format(ds))

    src_array = src_ds.GetRasterBand(1).ReadAsArray()

    return src_array


def apply_filter(xfilter, band):
    """Take in the target pixel value and apply a mask to the source data
    numpy array leaving only the target pixel values.

    Args:
        xfilter = the target class value (e.g. 608)
        band = numpy array generated from the source raster file

    Returns:
        None
    """

    band[band != xfilter] = 0

    return None


def get_xraster(xarray, ds):
    """Create a temporary raster from the masked numpy array

    Args:
        xarray = the masked numpy array
        ds = the original raster file path

    Returns:
        temp_raster = the full path to the masked raster file
    """

    # path to the temporary raster file
    path, fn = os.path.split(ds)

    # path.replace("\\", "/")
    temp_raster = "{}{}zzzz_band.tif".format(path, os.sep)

    src_ds = gdal.Open(ds)

    rows = src_ds.RasterYSize
    cols = src_ds.RasterXSize

    driver = gdal.GetDriverByName('GTiff')

    # GDALDriver::Create() method requires image size,
    # num. of bands, and band type
    outraster = driver.Create(temp_raster, cols, rows, 1, gdal.GDT_UInt16)

    if outraster is None:
        print("Could not create image file {a}".format
              (a=os.path.basename(temp_raster)))

        sys.exit(1)

    # =======================================================================
    # write numpy array to the raster========================================
    outband = outraster.GetRasterBand(1)
    outband.WriteArray(xarray, 0, 0)

    # =======================================================================
    # save data to the disk and set the nodata value=========================
    outband.FlushCache()
    outband.SetNoDataValue(255)

    # =======================================================================
    # georeference the image and set the projection==========================
    outraster.SetGeoTransform(src_ds.GetGeoTransform())
    outraster.SetProjection(src_ds.GetProjection())

    return temp_raster


def raster_to_shp(tempraster, newlayername):
    """Convert the masked raster data to a shapefile.  Delete the
    temporary raster file when finished.

    Args:
        tempraster = the full path to the masked raster file
        newlayername = name including full path to the output layer

    Returns:
        None
    """
    temp_ds = gdal.Open(tempraster)

    temp_band = temp_ds.GetRasterBand(1)

    prj = temp_ds.GetProjection()

    driver = ogr.GetDriverByName("ESRI Shapefile")

    outshpfile = driver.CreateDataSource(newlayername + ".shp")

    outlayer = outshpfile.CreateLayer(newlayername,
                                      srs=osr.SpatialReference(wkt=prj))

    gdal.Polygonize(temp_band, temp_band, outlayer, -1, [], callback=None)

    os.remove(tempraster)

    return None


def main_work(infile, outpath, classes):
    classvals = get_class_values(classes)

    for val in classvals:
        outlayer = get_outname(infile, outpath, val)

        if not os.path.exists(outlayer + ".shp"):

            srcarray = get_array(infile)

            apply_filter(val, srcarray)

            tempfile = get_xraster(srcarray, infile)

            print("Creating new shapefile for class %s" % val)

            print("Saving to %s" % os.path.split(outlayer)[0])

            raster_to_shp(tempfile, outlayer)

        else:
            print("%s .shp already exists" % outlayer)

    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-i", dest="infile", type=str, required=True,
                        help="The input thematic raster")

    parser.add_argument("-o", dest="outpath", type=str, required=True,
                        help="The full path to the output folder")

    parser.add_argument("-x", dest="classes", nargs="*", required=True,
                        help="The list of class values to polygonize")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == '__main__':
    t1 = get_time()

    main()

    t2 = get_time()

    print("\nProcessing time: %s" % (t2 - t1))
