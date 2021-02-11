#!/usr/bin/env python
#
# Adapted from the deepzoom_multiserver.py from https://github.com/openslide/openslide-python (Copyright (c) 2010-2015 Carnegie Mellon University)
# Major changes made:
# - Changed config to use variables in config.py instead of global variables here.
# - Dropped the classes for SlideImage and Directory.
# - Changed the endpoints to work with the projects structure.
# - Added a thumbnail endpoint.
#

import os
import urllib
import math

import slugify
import PIL
import xml.etree.ElementTree as ET 
import matplotlib.pyplot as plt

from io import BytesIO
from collections import OrderedDict
from threading import Lock


from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator
from flask import Flask, render_template, url_for, abort, make_response, request

from hover.src.external_infer_url import InfererURL, get_available_models


from config import *


app = Flask(__name__)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

class DZIFile(object):
    def __init__(self, path, raw_xml):
        self.path = path
        self.overlap = 0
        self.tile_size = 0
        self.height = 0
        self.width = 0
        
        self.raw_xml = raw_xml

        self.parse_xml()

    def parse_xml(self):

        root = ET.fromstring(self.raw_xml)
        
        self.overlap = int(root.attrib["Overlap"])
        self.tile_size = int(root.attrib["TileSize"])
        for child in root:
            print(child)
            if "Size" in child.tag:
                print(child.attrib)
                self.height = int(child.attrib["Height"])
                self.width = int(child.attrib["Width"])

    def get_associated_images(self, x, y, w, h, level):
        
        start_x = (x // self.tile_size)
        start_y = (y // self.tile_size)

        end_x = (x + w) // self.tile_size
        end_y = (y + h) // self.tile_size

        images = []
        for k in range(start_y, end_y + 2):
            column = []

            for i in range(start_x, end_x + 2):
                tile_file = str(i) + "_" + str(k) + "." + "jpeg"

                column.append(os.path.join(self.path + "_files", str(level), tile_file))

            images.append(column)

        return images

    def get_image(self, x, y, w, h, level):

        images = self.get_associated_images(x, y, w, h, level)

        new_image = PIL.Image.new('RGB', (self.tile_size * len(images[0]), self.tile_size*len(images)))

        y_idx = 0
        for row in images:
            x_idx = 0
            for img in row:
                tile = PIL.Image.open(img)
                new_image.paste(tile, (x_idx, y_idx))
                tile.close()

                x_idx += self.tile_size
            y_idx += self.tile_size

        start_x = x % self.tile_size
        start_y = y % self.tile_size

        new_image = new_image.crop(box=(start_x, start_y, start_x + w, start_y + h))

        return new_image


class _Cache(object):
    def __init__(self, cache_size):
        self.cache_size = cache_size
        self._lock = Lock()
        self._cache = OrderedDict()

    def get(self, path):
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                slide = self._cache.pop(path)
                self._cache[path] = slide
                return slide

        with open(path, 'rb') as fp:
            slide = DZIFile(path, fp.read())

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = slide
        return slide


class _TileCache(_Cache):
    def __init__(self, cache_size):
        super().__init__(cache_size)

    def get(self, path):
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                tile = self._cache.pop(path)
                self._cache[path] = tile
                return tile

        with open(path, 'rb') as fp:
            tile = fp.read()

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = tile
        return tile




@app.before_first_request
def load_slides():

    app.basedir = os.path.abspath(SLIDE_DIR)
    opts = {
        'tile_size': DEEPZOOM_TILE_SIZE,
        'overlap': DEEPZOOM_TILE_OVERLAP,
        'limit_bounds': DEEPZOOM_LIMIT_BOUNDS,
    }
    app.slidecache = _Cache(SLIDE_CACHE_SIZE)
    app.tilecache = _TileCache(SLIDE_CACHE_SIZE)
    app.slides = []
    app.tiffs = {}
    app.thumbnails = []

    for fname in os.listdir(app.basedir):
        if fname.endswith(".dzi"):
            app.slides.append(fname)
        if fname.endswith("_thumbnail.jpg"):
            app.thumbnails.append(fname)


@app.before_first_request
def get_models():

    app.inference_models = get_available_models(INFERENCE_URL)


def _get_slide(path):
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        # Directory traversal
        print("Path does not exist")
        abort(404)
    if not os.path.exists(path):
        print("File does not exist")
        abort(404)
    try:
        slide = app.slidecache.get(path)
        return slide
    except OpenSlideError:
        raise
        #abort(404)

def _get_tile(path, level, col, row, format):
    tile_file = str(col) + "_" + str(row) + "." + str(format)
    path = os.path.join(path + "_files", str(level), tile_file)
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        # Directory traversal
        print("Path does not exist")
        abort(404)
    if not os.path.exists(path):
        print("File does not exist")
        abort(404)
    try:
        slide = app.tilecache.get(path)
        return slide
    except:
        raise



@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", title="Home", files=app.slides)

@app.route('/slide/<path:path>')
def slide(path):
    print(app.slides)
    slide_url = url_for('dzi', path=path)
    return render_template('slide.html', slide_url=slide_url)


@app.route('/<path:path>.dzi')
def dzi(path):
    print(path)
    slide = _get_slide(path)
    resp = make_response(slide.raw_xml)
    resp.mimetype = 'application/xml'
    return resp


@app.route('/<path:path>_files/<int:level>/<int:col>_<int:row>.<ext>')
def tile(path, level, col, row, ext):
    
    ext = ext.lower()
    if ext != 'jpeg' and ext != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        path = "".join([path])
        tile = _get_tile(path, level, col, row, ext)
    except ValueError:
        # Invalid level or coordinates
        abort(404)

    resp = make_response(tile)
    resp.mimetype = 'image/%s' % ext
    return resp

@app.route
@app.route('/thumbnail/<path:path>')
def thumbnail(path):

    try:
        imgfile = os.path.splitext(path)[0]
        thumbnail = imgfile + "_thumbnail.jpg"

        if thumbnail not in app.thumbnails:
            raise KeyError

    except KeyError:
        abort(404)

    try:
        with open(os.path.abspath(os.path.join(app.basedir, thumbnail)), 'rb') as fp:
            resp = make_response(fp.read())
            resp.mimetype = 'image/%s' % 'jpg'
    except IOError:
        abort(404)
    return resp



@app.route('/annotate/<path:path>/<int:z>/<int:x>_<int:y>/<int:w>_<int:h>')
def annotate(path, z, x, y, w, h):

    slide = _get_slide(path)
    img = slide.get_image(x, y, w, h, z)

    infer = InfererURL(img, app.inference_models[0], server_url=INFERENCE_URL, profile='hv_pannuke')
    overlay = infer.run()
    overlay = overlay[:, :, 0]

    overlay = PIL.Image.fromarray(overlay, mode="P")
    img.putalpha(img.convert(mode="L"))

    plt.imshow(img)
    plt.imshow(overlay, alpha=0.5)

    try:
        buf = PILBytesIO()
        img.save(buf, format='jpeg')
        resp = make_response(buf.getvalue())
        resp.mimetype = 'image/%s' % 'jpeg'
    except:
        abort(500)

    return resp


if __name__ == "__main__":
    load_slides()
    app.debug = True
    app.run()
