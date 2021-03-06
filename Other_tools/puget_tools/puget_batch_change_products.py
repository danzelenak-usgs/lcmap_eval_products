"""Batch process Puget Sound mapped products:
1.  Clip and mosaic a pre-determined list of HV-tiles to the specified AOI shapefile
2.  Apply color maps to the ChangeMap and QAMap products
3.  Appy the reclassification and color mapping to the remaining change products
"""

import os
import argparse
import datetime as dt
import subprocess


def get_time():
    """
    Return the current time
    :return:
    """
    return dt.datetime.now()


def message(p):
    """

    :return:
    """
    print('\n{} process started at {:%Y-%m-%d %H:%M:%S}'.format(p, get_time()))

    return None


def main_work(change, cover, outdir, shp, ovr):
    """

    :param change:
    :param cover:
    :param outdir:
    :param shp:
    :param ovr:
    :return:
    """
    processes = ['Clip and mosaic', 'ChangeMap and QAMap color mapping', 'Reclassification and color mapping',
                 'Cover products']

    message(processes[0])

    subprocess.call([
        'python', 'Other_tools{sep}puget_tools{sep}puget_clip_mosaic_ccd.py'.format(sep=os.sep),
        '-i', change,
        '-o', outdir,
        '-shp', shp,
        '-ovr', ovr,
        '-f', 'change'
    ])

    subprocess.call([
        'python', 'Other_tools{sep}puget_tools{sep}puget_clip_mosaic_ccd.py'.format(sep=os.sep),
        '-i', cover,
        '-o', outdir,
        '-shp', shp,
        '-ovr', ovr,
        '-f', 'cover'
    ])

    to_color = ['ChangeMap', 'QAMap', 'CoverPrim', 'CoverSec']

    message(processes[1])

    for item in to_color:

        subprocess.call([
            'python', '1_apply_colormap.py',
            '-i', '{}{}{}'.format(outdir, os.sep, item),
            '-o', '{}{}{}'.format(outdir, os.sep, item),
            '-n', item,
            '-ovr', ovr
        ])

    to_reclass = {'ChangeMagMap': '1_reclassify_changemag.py', 'LastChange': '1_reclassify_lastchange.py',
                  'SegLength': '1_reclassify_seglength.py'}

    message(processes[2])

    for key in to_reclass:

        subprocess.call([
            'python', to_reclass[key],
            '-i', '{}{}{}'.format(outdir, os.sep, key),
            '-o', '{}{}{}'.format(outdir, os.sep, key),
            '-ovr', ovr
        ])

        reclass_out = '{out}{sep}{k}{sep}{k}_reclass'.format(out=outdir, sep=os.sep, k=key)

        subprocess.call([
            'python', '1_apply_colormap.py',
            '-i', reclass_out,
            '-o', '{}{}{}'.format(outdir, os.sep, key),
            '-n', key,
            '-ovr', ovr
        ])



def main():
    """

    :return:
    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-change', dest='change', required=True, type=str,
                        help='The full path to the root directory of HV subfolders '
                             'containing the mapped change products')

    parser.add_argument('-cover', dest='cover', required=False, type=str,
                        help='The full path to the root directory of HV subfolders '
                             'containing the mapped cover products')

    parser.add_argument('-o', dest='outdir', required=True, type=str,
                        help='The full path to the root output directory')

    parser.add_argument('-shp', dest='shp', required=True, type=str,
                        help='The full path including filename of the AOI shapefile')

    parser.add_argument('-ovr', dest='ovr', required=True, default='False', type=str,
                        help='Specify whether or not to overwrite previously existing outputs')

    args = parser.parse_args()

    main_work(**vars(args))


if __name__ == '__main__':
    t1 = get_time()

    main()

    t2 = get_time()

    print("\nTotal processing time: {}".format(str(t2 - t1)))
