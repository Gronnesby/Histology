
import os
import urllib
import tempfile

from flask import Flask, render_template, url_for, abort, make_response, request
from slide_reader import SlideImage
from io import BytesIO
from PIL import Image

from config import THUMBNAIL_SIZE

APP = Flask(__name__)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

def load_images():

    APP.config['pathology_images_path'] = 'static/images/pathology'
    APP.list_of_files = {}
    APP.slugs = {}

    for (dirpath, _, filenames) in os.walk('static/images/pathology'):
        for filename in filenames:
            if filename.endswith('.vms'):
                APP.list_of_files[filename] = SlideImage(os.sep.join([dirpath, filename]))
                slug = filename.split(' ')[0]
                slug = os.path.splitext(slug)[0]
                APP.slugs[slug] = filename

APP.before_first_request(load_images)

@APP.route('/')
@APP.route('/index')
def index():
    return render_template("index.html", title="Home")

def create_thumbnail(imagefile):

    try:
        im = Image.open(os.path.join(APP.config['pathology_images_path'], imagefile))
        im.thumbnail(THUMBNAIL_SIZE)
        outfile = imagefile.replace("_map2.jpg", "_thumbnail.jpg")
        im.save(os.path.join(APP.config['pathology_images_path'], outfile), "JPEG")
    except IOError:
        print("cannot create thumbnail for", imagefile)

@APP.context_processor
def images():
    return dict(images=sorted(APP.slugs))


@APP.route('/test')
def test():
    return render_template("404.html")


@APP.route('/image')
def image():

    slug = request.args.get('slug')
    try:
        filename = APP.slugs[slug]
        img = APP.list_of_files[filename]
    except KeyError:
        render_template("404.html")

    height = img.osr.dimensions[1]
    width = img.osr.dimensions[0]

    z = 1.0
    x = width/2
    y = height/2
    w = width
    h = height

    if 'z' in request.args:
        z = float(request.args.get('level'))
    if 'x' in request.args:
        x = float(request.args.get('x'))
    if 'y' in request.args:
        y = float(request.args.get('y'))
    if 'w' in request.args:
        w = float(request.args.get('w'))
    if 'h' in request.args:
        h = float(request.args.get('h'))

    return render_template("slide.html", imgheight=height, imgwidth=width, slug=slug, x=x, y=y, z=z, w=w, h=h, tileSize=img.TILE_SIZE+2)

@APP.route('/map')
def map():

    slug = request.args.get('slug')

    try:
        filename = APP.slugs[slug]

        imgfile = os.path.splitext(filename)[0]
        thumbnail = imgfile + "_thumbnail.jpg"

    except KeyError:
        raise

    try:
        with open((os.path.join(APP.config['pathology_images_path'], thumbnail)), 'rb') as fp:
            resp = make_response(fp.read())
            resp.mimetype = 'image/%s' % 'jpg'
    except IOError:
        raise
    return resp


@APP.route('/tile')
def tile():

    slug = str(request.args.get('slug'))
    z = int(request.args.get('level'))
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))

    try:
        filename = APP.slugs[slug]
        tileimage = APP.list_of_files[filename].get_tile(z, (x, y))
    except KeyError:
        raise

    buf = PILBytesIO()
    tileimage.save(buf, 'jpeg')
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % 'jpeg'
    return resp

@APP.route('/annotate')
def annotate():

    slug = str(request.args.get('slug'))
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    h = int(request.args.get('h'))
    w = int(request.args.get('w'))
    z = int(request.args.get('level'))

    try:
        filename = APP.slugs[slug]
        img = APP.list_of_files[filename]
    except KeyError:
        return render_template('404.html')
    

    overlay = img.infer((x, y), z, (w, h))
    
    buf = PILBytesIO()
    overlay.convert("P", palette=Image.ADAPTIVE, colors = 4).save(buf, 'png')
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % 'png'

    return resp


@APP.route('/thumbnail')
def thumbnail():
    
    slug = str(request.args.get('slug'))
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    h = int(request.args.get('h'))
    w = int(request.args.get('w'))
    z = int(request.args.get('level'))


    try:
        filename = APP.slugs[slug]
        thumb = APP.list_of_files[filename].get_image((x, y), z, (w, h))
    except KeyError:
        raise

    buf = PILBytesIO()
    thumb.save(buf, 'png')
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % 'png'

    return resp

if __name__ == "__main__":
    load_images()
    APP.run()
