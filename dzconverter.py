
import os
import re
import sys
import pyvips as vips

import json
import xmltodict



def _dzconvert_aperio(filename, outname):

    try:

        img = vips.Image.new_from_file(filename)
    except:
        print("Could not open file {0}".format(filename))
        raise

    mpp_meta = img.get('aperio.MPP')
    
    basename = os.path.splitext(filename)[0]
    basedir = os.path.dirname(basename)
    dzfname = os.path.join(basedir, outname)
    
    img.dzsave(dzfname)

    with open(dzfname + ".dzi", 'r') as fp:
        data_dict = xmltodict.parse(fp.read())

    json_data = json.dumps(data_dict)
    json_data = json.loads(re.sub('@+', '', json_data))

    json_data["Image"]["mpp"] = mpp_meta

    with open(dzfname + ".dzi", 'w') as fp:
        fp.write(json.dumps(json_data))

    os.rename(dzfname + "_files", dzfname + ".dzi" + "_files")


def _dzconvert_mirax(filename, outname):

    try:
        img = vips.Image.new_from_file(filename)
    except:
        print("Could not open file {0}".format(filename))
        raise


def dzconvert(filename, outname):


    if filename.endswith('.svs'):
        _dzconvert_aperio(filename, outname)

    if filename.endswith('.mrxs'):
        _dzconvert_mirax(filename, outname)



if __name__ == "__main__":


    if len(sys.argv) < 3:
        print("Usage: dzconverter.py <input_image> <output_name>")
        sys.exit(1)
    else:
        dzconvert(sys.argv[1], sys.argv[2])

    