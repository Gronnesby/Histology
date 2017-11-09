
import os

from flask import Flask, render_template, url_for, abort, make_response, request
from slide_reader import SlideImage
from io import BytesIO
from PIL import Image

APP = Flask(__name__)
THUMBNAIL_SIZE = 500, 500

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

@APP.route('/')
@APP.route('/index')
def index():
    return render_template("index.html", title="Home")


def load_images():

    APP.config['pathology_images_path'] = './static/images/pathology'
    APP.list_of_files = {}
    APP.slugs = {}
    for (dirpath, _, filenames) in os.walk('static/images/pathology'):
        for filename in filenames:
            if filename.endswith('.vms'):
                APP.list_of_files[filename] = SlideImage(os.sep.join([dirpath, filename]))
                slug = filename.split(' ')[0]
                slug = os.path.splitext(slug)[0]
                APP.slugs[slug] = filename

def create_thumbnail(imagefile):

    try:
        im = Image.open(os.path.join(APP.config['pathology_images_path'], imagefile))
        im.thumbnail(THUMBNAIL_SIZE)
        outfile = imagefile.replace("_map2.jpg", "_thumbnail.jpg")
        im.save(os.path.join(APP.config['pathology_images_path'], outfile), "JPEG")
    except IOError:
        print "cannot create thumbnail for", imagefile

@APP.context_processor
def images():

    return dict(images=sorted(APP.slugs))

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

    return render_template("slide.html", imgheight=height, imgwidth=width, slug=slug)

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

    print slug, z, x, y
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


@APP.route('/case')
def case():

    slug = str(request.args.get('slug'))

    return render_template("case.html", slug=slug)

if __name__ == "__main__":

    APP.debug = True
    load_images()
    APP.run(host='0.0.0.0', port=5000)
