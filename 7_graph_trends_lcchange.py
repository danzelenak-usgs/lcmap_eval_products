# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate vertical bar charts and tables of Trends LC Change
for specific years.

"""

import os, sys, glob
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame

#%%
def get_rasters(indir):

    """Purpose: Construct a string pointing to a specific land cover from-to
    raster, and check to make sure that it exists.

    Args:
        indir = string, the input directory containing the from-to rasters

    Returns:
        in_cl = string, the full path to the input from-to raster file.
    """

    in_cl = glob.glob(indir + os.sep + "*.tif")

    if in_cl is None:

        print("\n**Could not locate input LC Change file for the years specified**\n")

        sys.exit(1)

    return in_cl

#%%
def read_data(cl):

    """
    Purpose: Open the Trends from-to LC Change .tif file.
                Iterate through the list of from-to classes.
                Calculate the number of pixels for each from-to class.
                Call the get_trends_area function to calculate the total number
                    of Trends pixels in the tile
    Args:
        cl = string, the full path to the Trends from-to .tif file

    Returns:
        classes = list, the Trends from-to classes
        masked_sum = list, the total number of pixels for each class
        total_pixels = the total number of Trends pixels in the tile
    """

    cl_src = gdal.Open(cl, gdal.GA_ReadOnly)

    cl_data = cl_src.GetRasterBand(1).ReadAsArray()

    # these are valid for the Trends classes
    classes = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 201, 202,
               203, 204 ,205, 206, 207, 208, 209, 210, 211, 301, 302, 303, 304,
               305, 306, 307, 308, 309, 310, 311, 401, 402, 403, 404, 405, 406,
               407, 408, 409, 410, 411, 501, 502, 503, 504, 505, 506, 507, 508,
               509, 510, 511, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610,
               611, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 801,
               802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 901, 902, 903,
               904, 905, 906, 907, 908, 909, 910, 911, 1001, 1002, 1003, 1004,
               1005, 1006, 1007, 1008, 1009, 1010, 1011, 1101, 1102, 1103, 1104,
               1105, 1106, 1107, 1108, 1109, 1110, 1111]

    # classes = np.unique(cl_data)

    masked_sum = []

    for c in classes:

        mask_cl = np.copy(cl_data)

        mask_cl[mask_cl != c] = 0
        mask_cl[mask_cl == c] = 1

        holder = np.sum(mask_cl)

        masked_sum.append(holder)

        # gives an idea of progress for the user
        print(c, " ", holder)

    total_pixels = get_trends_area(cl_data)

    cl_data, cl_src, mask_cl = None, None, None

    return classes, masked_sum, total_pixels

#%%
def get_trends_area(data):

    """Purpose:  Calculate the area of coverage by Trends within the ARD tile,
    which will be used to calculate the percentage for each Trends From-To class.

    Args:
        data = numpy array, the input data

    Returns:
        count = integer, the calculated area covered by trends (actually the
        number of trends pixels)
    """

    mask_data = np.copy(data)

    mask_data[mask_data > 0] = 1
    mask_data[mask_data <= 0] = 0

    count = np.sum(mask_data)

    return count

#%%
def get_figure(label_set, df, tile, year1, year2, outname):

    """Purpose: Generate a matplotlib figure of n rows and 2 columns, the number
                rows is equal to the number of classes (label_set).  Column 1
                will contain vertical bar charts colored by the 'from' class.
                Column 2 will contain tables showing the count and percent for
                row n 'from' class.
    Args:
        label_set = list of classes
        df = pandas DataFrame object contains class names, counts, and percents
        tile = string, the name of the ARD tile
        year1, year2 = strings, the from and to years
        outname = the output path and filename for the .png image
    Returns:
        None
    """

    # RGB colors taken from Arc colormap and rescaled from 0-255 to 0-1
    colors = {"1" : (0.0, 0.0, 0.9333333333333333),
          "2" : (0.9019607843137255, 0.0, 0.058823529411764705),
          "3" : (0.9333333333333333, 0.0, 0.9333333333333333),
          "4" : (0.129, 0.129, 0.129),
          "5" : (0.7019607843137254, 0.7019607843137254, 0.7019607843137254),
          "6" : (0.0, 0.5294117647058824, 0.10980392156862745),
          "7" : (0.9333333333333333, 0.9333333333333333, 0.25098039215686274),
          "8" : (0.9333333333333333, 0.592156862745098, 0.0),
          "9" : (0.0, 0.9215686274509803, 0.9215686274509803),
          "10" : (0.004, 0.1098, 0.4745),
          "11" : (0.2901960784313726, 0.43137254901960786, 0.6392156862745098)}

    # Generate figure with length(label_set) rows and 2 columns
    fig, axes = plt.subplots(nrows = len(label_set), ncols = 2,
                                  figsize=(16, 50))

    # Add figure title
    fig.suptitle("%s Trends %s to %s From-To Classes" % (tile, year1, year2),
                 fontsize=22, fontweight="bold")

    for i, L in enumerate(label_set):

        t = []

        # iterate through rows of dataframe to retrieve values for class L
        for x in df.itertuples():

            if x[1][0] == L and len(x[1]) == 3:

                t.append(x[1:])

            elif x[1][:2] == L and len(x[1]) == 4:

                t.append(x[1:])

        df_temp = DataFrame(t)

        # print(df_temp)

        # Assign column names
        df_temp.columns = ["Name", "Count", "Percent of Trends Coverage"]

        # generate bar charts in first column for class L in row i
        axes[i, 0].bar(df_temp.index, df_temp.Count, facecolor=colors[L])
        axes[i, 0].set_title('"From" Class ' + L + " Bar Chart")
        axes[i, 0].set_xticks(df_temp.index)
        axes[i, 0].set_xticklabels(df_temp.Name)
        axes[i, 0].set_xlabel("Class")
        axes[i, 0].set_ylabel("Count")

        # generate tables in second column for class L in row i
        axes[i, 1].table(cellText=df_temp.values, bbox=[0,0,1,1], colLabels=df_temp.columns)
        axes[i, 1].set_title('"From" Class ' + L + " Table")
        axes[i, 1].set_xticks([])
        axes[i, 1].set_yticks([])

    plt.tight_layout()
    plt.subplots_adjust(top=0.95)

    # save the figure to a .png file
    plt.savefig(outname, bbox_inches="tight", dpi=150)

    return None

#%%
def usage():
    print("\n\t[-i the full path to the folder containing the input raster file]\n"\
    "\t[-o the full path to the output graph image (.png)]\n"\
    "\t[-tile the tile name (used for graph title)]\n"\
    "\t[-frm the from year]\n"\
    "\t[-to the to year]\n"\
    "\t[-help display this message]\n")

    print("Example: python graph_nlcd.py -i C:\... -o C:\... -tile h05v02 "\
          "-name trends -frm 1992 -to 2011")

#%%
def main():

    argv = sys.argv

    if len(argv) <= 1:

        print("***Missing required arguments***\n")

        print("Try using -help\n")

        sys.exit(0)

    i = 1

    while i < len(argv):

        arg = argv[i]

        if arg == "-i":
            i = i + 1
            in_dir = argv[i]

        elif arg == "-o":
            i = i + 1
            out_dir = argv[i]

        elif arg == "-tile":
            i = i + 1
            tile = argv[i]

        elif arg == "-frm":
            i = i + 1
            year1 = argv[i]

        elif arg == "-to":
            i = i + 1
            year2 = argv[i]

        elif arg == "-help":
            i = i + 1
            usage()
            sys.exit(1)

        i += 1

    # just some values used for testing
    # tile = "h02v09"
    # in_dir = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h02v09\reference_data"
    # year1 = "1992"
    # year2 = "2011"
    # out_dir = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h02v09\graphs\test"

    if not os.path.exists(out_dir): os.mkdir(out_dir)

    in_files = get_rasters(in_dir)
    
    for in_cl in in_files:

        year1 = in_cl[-12:-10]
        year2 = in_cl[-8:-6]
                
        outname = "%s%s%strends%sto%s_lchange.png" % (out_dir, os.sep, tile, year1, year2)
        
        classes, class_sums, total = read_data(in_cl)
    
        # calculate the percent of the total for each from-to class
        class_perc= ["%.2f" % (val / float(total) * 100.0) for val in class_sums]
    
        # convert the items in classes list to strings and save in a new list
        labels = [str(c) for c in classes]
    
        # get a set of the unique "from" classes (the first 1 or 2 digits)
        labels_ =  [l[0] if len(l)==3 else l[:2] for l in labels]
        label_set = set(labels_) # converting to set removes duplicates
        label_set = list(label_set) # convert back to list to allow indexing
    
        # Cluttered way to return a list of class values with the correct order
        label_set = [int(l) for l in label_set]
        label_set.sort()
        label_set = [str(l) for l in label_set]
    
        # create list of tuples to populate three data columns
        data = [(x,y,z) for x,y,z in zip(labels, class_sums, class_perc)]
    
        # create pandas dataframe from the list of tuples
        df = DataFrame(data)
    
        # add column names to the dataframe
        df.columns = ["Name", "Count", "Percent"]
    
        get_figure(label_set, df, tile, year1, year2, outname)

    return None

#%%
if __name__ == "__main__":

    main()