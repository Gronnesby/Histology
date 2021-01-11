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
from io import BytesIO
from collections import OrderedDict
from threading import Lock

from PIL import Image
from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator
from flask import Flask, render_template, url_for, abort, make_response, request

from config import *


app = Flask(__name__)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

class _SlideCache(object):
    def __init__(self, cache_size, dz_opts):
        self.cache_size = cache_size
        self.dz_opts = dz_opts
        self._lock = Lock()
        self._cache = OrderedDict()

    def get(self, path):
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                slide = self._cache.pop(path)
                self._cache[path] = slide
                return slide

        osr = OpenSlide(path)
        slide = DeepZoomGenerator(osr, **self.dz_opts)

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = slide
        return slide


def load_slides():

    app.basedir = os.path.abspath(SLIDE_DIR)
    opts = {
        'tile_size': DEEPZOOM_TILE_SIZE,
        'overlap': DEEPZOOM_TILE_OVERLAP,
        'limit_bounds': DEEPZOOM_LIMIT_BOUNDS,
    }
    app.cache = _SlideCache(SLIDE_CACHE_SIZE, opts)
    app.slides = []
    app.thumbnails = []

    for fname in os.listdir(app.basedir):
        if fname.endswith(".vms"):
            app.slides.append(fname)
        if fname.endswith("_thumbnail.jpg"):
            app.thumbnails.append(fname)


def _get_slide(path):
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        # Directory traversal
        abort(404)
    if not os.path.exists(path):
        abort(404)
    try:
        slide = app.cache.get(path)
        slide.filename = os.path.basename(path)
        return slide
    except OpenSlideError:
        abort(404)


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", title="Home", files=app.slides)

@app.route('/slide/<path:path>')
def slide(path):
    slide_url = url_for('dzi', path=path)
    return render_template('slide.html', slide_url=slide_url)


@app.route('/<path:path>.dzi')
def dzi(path):
    slide = _get_slide(path)
    resp = make_response(slide.get_dzi(DEEPZOOM_FORMAT))
    resp.mimetype = 'application/xml'
    return resp


@app.route('/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
def tile(path, level, col, row, format):
    slide = _get_slide(path)
    format = format.lower()
    if format != 'jpeg' and format != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        tile = slide.get_tile(level, (col, row))
    except ValueError:
        # Invalid level or coordinates
        abort(404)
    buf = PILBytesIO()
    tile.save(buf, format, quality=DEEPZOOM_TILE_QUALITY)
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % format
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
