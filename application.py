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
import sys
import warnings
import uuid
import base64

warnings.filterwarnings("ignore")

import numpy as np
import json
import PIL

from io import BytesIO
from collections import OrderedDict
from threading import Lock


from flask import Flask, render_template, url_for, abort, make_response, jsonify

from hover_serving.src.external_infer_url import InfererURL, get_available_models


from config import *


app = Flask(__name__)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

class DZIFile(object):
    def __init__(self, path, raw_json):
        self.path = path
        self.overlap = 0
        self.tile_size = 0
        self.height = 0
        self.width = 0
        self.mpp = 0
        
        self.raw_json = raw_json

        self.parse_json()

    def parse_json(self):

        root = json.loads(self.raw_json)
        image_meta = root["Image"]
        
        self.overlap = int(image_meta["Overlap"])
        self.tile_size = int(image_meta["TileSize"])
        self.height = int(image_meta["Size"]["Height"])
        self.width = int(image_meta["Size"]["Width"])
        self.mpp = float(image_meta["mpp"])

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

    def get_image(self, x, y, w, h, level, downsample=False):

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
        if downsample:
            new_image = new_image.resize((int(w/app.downsampling), int(h/app.downsampling)), resample=PIL.Image.LANCZOS)
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
    except e:
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

    app.annotations = {}

@app.before_first_request
def get_models():

    try:
        app.inference_models = get_available_models(INFERENCE_URL)
        app.model = app.inference_models[0]
    except Exception as e:
        print(f"Got exception {e}")
        print(f"Setting model to pannuke_original")
        app.model = "pannuke_original"
        app.inference_models = [app.model]


@app.before_first_request
def set_downsampling():

    app.downsampling_levels = [1, 2, 4, 8]
    app.downsampling = app.downsampling_levels[2]


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", title="Home", files=app.slides, models=app.inference_models)

@app.route('/slide/<path:path>')
def slide(path):
    print(app.slides)
    slide_url = url_for('dzi', path=path)
    return render_template('slide.html', slide_url=slide_url, models=app.inference_models)


@app.route('/<path:path>.dzi')
def dzi(path):

    slide = _get_slide(path)
    resp = make_response(slide.raw_json)
    resp.mimetype = 'application/json'
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


@app.route('/thumbnail/<path:path>')
def thumbnail(path):

    print(path)
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




def base64_encode_image(imgbytes):

    encoded_image = base64.encodebytes(imgbytes.getvalue()).decode('ascii')
    encoded_image = 'data:image/png;base64,' + encoded_image
    return encoded_image


@app.route('/annotate/<path:path>/<int:z>/<int:x>_<int:y>/<int:w>_<int:h>', defaults={"model": None})
@app.route('/annotate/<path:path>/<int:z>/<int:x>_<int:y>/<int:w>_<int:h>/<string:model>')
def annotate(path, z, x, y, w, h, model):

    if model is not None and model in app.inference_models:
        app.model = model

    slide = _get_slide(path)
    app.downsampling = 1
    img = slide.get_image(x, y, w, h, z, downsample=False)

    infer = InfererURL(img, app.model, server_url=INFERENCE_URL)
    pred, counts = infer.run_type()
    overlay = np.zeros((pred.shape[0], pred.shape[1], 4), dtype=np.uint8)
    
    app.cell_types = {v:k for k, v in infer.nuclei_types.items()}
    
    for i in range(overlay.shape[0]):
        for j in range(overlay.shape[1]):

            if pred[i,j,0] == 0:
                color = [0,0,0,0]
            else:
                color = list(infer.color_mapping[pred[i,j,0]])
                color.append(180)

            overlay[i, j] = color

    im = PIL.Image.fromarray(overlay, mode="RGBA")

    try:

        buf = PILBytesIO()
        im.save(buf, format='png')
        encoded_img = base64_encode_image(buf)

        resp_data = {"img": encoded_img, "meta": {k: [int(v), infer.colors[k]] for k, v in counts.items()}}

        resp = make_response(json.dumps(resp_data))
        resp.mimetype = 'application/json'

    except:
        raise

    return resp


@app.route('/modelinfo/<string:name>')
def models(name):

    try:
        resp = make_response(json.dumps(app.inference_models))
        resp.mimetype = 'application/json'
    except:
        raise

    return resp


if __name__ == "__main__":
    load_slides()
    app.debug = False
    app.run()
