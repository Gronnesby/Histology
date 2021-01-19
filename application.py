#!/usr/bin/env python
#
# Adapted from the deepzoom_multiserver.py from https://github.com/openslide/openslide-python (Copyright (c) 2010-2015 Carnegie Mellon University)
# Major changes made:
# - Changed config to use variables in config.py instead of global variables here.
# - Dropped the classes for SlideImage and Directory.
# - Changed the endpoints to work with the projects structure.
# - Added a thumbnail endpoint.
#
# 
#
#

import os
import urllib
import tempfile
import slugify
import PIL
from io import BytesIO
from collections import OrderedDict
from threading import Lock


from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator
from flask import Flask, render_template, url_for, abort, make_response, request

from config import *


app = Flask(__name__)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

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
            slide = fp.read()
        

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

        try:
            tile = PIL.Image.open(path)
        except PIL.UnidentifiedImageError:
            raise

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
    app.tilecache = _Cache(SLIDE_CACHE_SIZE)
    app.slides = []
    app.thumbnails = []

    for fname in os.listdir(app.basedir):
        if fname.endswith(".dzi"):
            app.slides.append(fname)
        if fname.endswith("_thumbnail.jpg"):
            app.thumbnails.append(fname)


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
    resp = make_response(slide)
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

    print("Path: {0}".format(path))
    slide = _get_slide(path)
    osr = slide._osr

    coord = (x, y)
    dim = (w, h)

    level = osr.get_best_level_for_downsample(DEEPZOOM_DOWNSAMPLE_FACTOR)

    print("Level: {0} Z: {1} z/levelcount: {2}".format(level, z, z/osr.level_count))
    print("W, H: {0} X, Y: {1} Z: {2} level: {3} downsample: {4} level_count: {5}".format(dim, coord, z, level, DEEPZOOM_DOWNSAMPLE_FACTOR, osr.level_count))

    dim = (int(dim[0]/DEEPZOOM_DOWNSAMPLE_FACTOR), int(dim[1]/DEEPZOOM_DOWNSAMPLE_FACTOR))
    image = osr.read_region(coord, level, dim)

    try:
        buf = PILBytesIO()
        image.save(buf, 'png')
        resp = make_response(buf.getvalue())
        resp.mimetype = 'image/%s' % 'png'
    except:
        abort(500)

    return resp


if __name__ == "__main__":
    load_slides()
    app.debug = True
    app.run()
