# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate vertical bar charts and tables of NLCD LC Change
for specific years.

"""

import argparse
import glob
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal
from pandas import DataFrame


# %%
def get_rasters(indir):
    in_cl = glob.glob(indir + os.sep + "*.tif")

    if in_cl is None:
        print("\n**Could not locate input LC Change file for the years specified**\n")

        sys.exit(1)
    # in_ct = glob.glob(indir + os.sep + "NLCD_NumChanges" + os.sep + "nlcd{}to{}ct.tif".format(y1, y2))[0]

    return in_cl  # , in_ct


# %%
def read_data(cl, type='original'):
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
    # count_src = gdal.Open(count, gdal.GA_ReadOnly)

    cl_data = cl_src.GetRasterBand(1).ReadAsArray()
    # count_data = count_src.GetRasterBand(1).ReadAsArray()


    # these are valid for the NLCD recoded classes, use np.unique below
    # to ignore empty classes if desired

    classes_recode = [101, 102, 105, 106, 107, 108, 109, 111, 181, 201, 202, 205, 206,
               207, 208, 209, 211, 281, 501, 502, 505, 506, 507, 508, 509, 511,
               581, 601, 602, 605, 606, 607, 608, 609, 611, 681, 701, 702, 705,
               706, 707, 708, 709, 711, 781, 801, 802, 805, 806, 807, 808, 809,
               811, 881, 901, 902, 905, 906, 907, 908, 909, 911, 981, 1101,
               1102, 1105, 1106, 1107, 1108, 1109, 1111, 1181, 8101, 8102,
               8105, 8106, 8107, 8108, 8109, 8111, 8181]

    classes_original = np.unique(cl_data)

    masked_sum = []

    if type=='original':

        classes = classes_original

    else:

        classes= classes_recode

    for c in classes:
        mask_cl = np.copy(cl_data)

        mask_cl[mask_cl != c] = 0
        mask_cl[mask_cl == c] = 1

        holder = np.sum(mask_cl)

        masked_sum.append(holder)

        # gives an idea of progress for the user
        print(c, " ", holder)

    cl_data, cl_src, mask_cl = None, None, None

    return classes, masked_sum


# %%
def get_figure(label_set, df, tile, year1, year2, outname, type='original'):
    """Purpose: Generate a matplotlib figure of n rows and 2 columns, the number
                rows is equal to the number of classes (label_set).  Column 1
                will contain vertical bar charts colored by the 'from' class.
                Column 2 will contain tables showing the count and percent for
                row n 'from' class.
    Args:
        label_set = list, list of classes
        df = pandas DataFrame object contains class names, counts and percents
        tile = string, the name of the ARD tile
        year1, year2 = strings, the from and to years
        outname = the output path and filename for the .png image
    Returns:
        None
    """

    # RGB colors taken from Arc colormap and rescaled from 0-255 to 0-1

    colors_recode = {"1": (0.0, 0.0, 0.9333333333333333),
                     "2": (0.9019607843137255, 0.0, 0.058823529411764705),
                     "5": (0.7019607843137254, 0.7019607843137254, 0.7019607843137254),
                     "6": (0.0, 0.5294117647058824, 0.10980392156862745),
                     "7": (0.9333333333333333, 0.9333333333333333, 0.25098039215686274),
                     "8": (0.9333333333333333, 0.592156862745098, 0.0),
                     "9": (0.0, 0.9215686274509803, 0.9215686274509803),
                     "11": (0.2901960784313726, 0.43137254901960786, 0.6392156862745098),
                     "81": (0.3333333333333333, 1.0, 0.0)}

    colors_orig = {"11": (0.278431373, 0.419607843, 0.62745098),
                   "12": (0.819607843, 0.866666667, 0.976470588),
                   "21": (0.866666667, 0.788235294, 0.788235294),
                   "22": (0.847058824, 0.576470588, 0.509803922),
                   "23": (0.929411765, 0.00, 0.00),
                   "24": (0.666666667, 0.00, 0.00),
                   "31": (0.698039216, 0.678431373, 0.639215686),
                   "41": (0.407843137, 0.666666667, 0.388235294),
                   "42": (0.109803922, 0.388235294, 0.188235294),
                   "43": (0.709803922, 0.788235294, 0.556862745),
                   "51": (0.647058824, 0.549019608, 0.188235294),
                   "52": (0.8, 0.729411765, 0.48627451),
                   "71": (0.88627451, 0.88627451, 0.756862745),
                   "72": (0.788235294, 0.788235294, 0.466666667),
                   "73": (0.6, 0.756862745, 0.278431373),
                   "74": (0.466666667, 0.678431373, 0.576470588),
                   "81": (0.858823529, 0.847058824, 0.239215686),
                   "82": (0.666666667, 0.439215686, 0.156862745),
                   "90": (0.729411765, 0.847058824, 0.917647059),
                   "95": (0.439215686, 0.639215686, 0.729411765)}

    # Generate figure with length(label_set) rows and 2 columns
    fig, axes = plt.subplots(nrows=len(label_set), ncols=2,
                             figsize=(16, 50))

    # Add figure title
    fig.text(0.5, .90, "%s NLCD %s to %s From-To Classes" % (tile, year1, year2),
             horizontalalignment="center", fontsize=22, fontweight='bold')

    for i, L in enumerate(label_set):

        t = []

        # iterate through rows of dataframe to retrieve values for class L
        for x in df.itertuples():

            if x[1][0] == L and len(x[1]) == 3:

                t.append(x[1:])

            elif x[1][:2] == L and len(x[1]) == 4:

                t.append(x[1:])

        df_temp = DataFrame(t)

        # Assign column names
        df_temp.columns = ["Name", "Count", "Percent of Tile"]

        # generate bar charts in first column for class L in row i
        if type=='original':

            axes[i, 0].bar(df_temp.index, df_temp.Count, width=0.8, facecolor=colors_orig[L])

        else:

            axes[i, 0].bar(df_temp.index, df_temp.Count, width=0.8, facecolor=colors_recode[L])

        axes[i, 0].set_title('"From" Class ' + L + " Bar Chart")
        axes[i, 0].set_xticks(df_temp.index)
        axes[i, 0].set_xticklabels(df_temp.Name)
        axes[i, 0].set_xlabel("Class")
        axes[i, 0].set_ylabel("Count")

        # generate tables in second column for class L in row i
        axes[i, 1].table(cellText=df_temp.values, bbox=[0, 0, 1, 1], colLabels=df_temp.columns)
        axes[i, 1].set_title('"From" Class ' + L + " Table")
        axes[i, 1].set_xticks([])
        axes[i, 1].set_yticks([])

    # save the figure as a .png file
    plt.savefig(outname, bbox_inches="tight", dpi=150)

    return None


# %%
def usage():
    print("\n\t[-i the full path to the input raster file]\n"
          "\t[-o the full path to the output graph image (.png)]\n"
          "\t[-tile the tile name (used for graph title)]\n"
          "\t[-frm the from year]\n"
          "\t[-to the to year]\n"
          "\t[-help display this message]\n")

    print("Example: python graph_nlcd.py -i C:\... -o C:\... -tile h05v02 "
          "-name trends -frm 1992 -to 2011")


# %%
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', type=str, required=True,
                        help='The full path to the input raster file')

    parser.add_argument('-o', '--output', type=str, required=True,
                        help='The full path to the output graph image (.png)')

    parser.add_argument('-t', '--tile', type=str, required=True,
                        help='The tile name (used for graph title)')

    parser.add_argument('-type', '--type', type=str, required=False, choices=['original', 'recode'],
                        help='Use either original or recoded NLCD values (use original by default)')

    # TODO remove these arguments probably
    parser.add_argument('-to', '--to', type=str, required=False,
                        help='The time segment end year')

    parser.add_argument('-frm', '-from', '--from', type=str, required=False,
                        help='The time segment beginning year')

    args = parser.parse_args()

    out_dir = args.output

    in_dir = args.input

    tile = args.tile

    type=args.type

    if not os.path.exists(out_dir): os.mkdir(out_dir)

    in_files = get_rasters(in_dir)

    for in_cl in in_files:
        year1 = in_cl[-12:-10]
        year2 = in_cl[-8:-6]

        outname = "{}{}{}_nlcd{}to{}_lchange.png".format(out_dir, os.sep, tile, year1, year2)

        classes, class_sums = read_data(in_cl, type)

        # calculate the percent of the total for each from-to class
        class_perc = ["%.2f" % (val / 25000000.0 * 100.0) for val in class_sums]

        # convert the items in classes list to strings and save in a new list
        labels = [str(c) for c in classes]

        # get a set of the unique "from" classes (the first 1 or 2 digits)
        labels_ = [l[0] if len(l) == 3 else l[:2] for l in labels]
        label_set = set(labels_)  # converting to set removes duplicates
        label_set = list(label_set)  # convert back to list to allow indexing

        # Cluttered way to return a list of class values with the correct order
        label_set = [int(l) for l in label_set]
        label_set.sort()
        label_set = [str(l) for l in label_set]

        # create list of tuples to populate three data columns
        data = [(x, y, z) for x, y, z in zip(labels, class_sums, class_perc)]

        # create pandas dataframe from the list of tuples
        df = DataFrame(data)

        # add column names to the dataframe
        df.columns = ["Name", "Count", "Percent"]

        get_figure(label_set, df, tile, year1, year2, outname, type)

    return None


# %%
if __name__ == "__main__":
    main()
