
import os

from flask import Flask, render_template, url_for, abort, make_response, jsonify
from slide_reader import SlideImage
from io import BytesIO

APP = Flask(__name__)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')

@APP.route('/')
@APP.route('/index')
def index():
    return render_template("index.html", title="Home")

def load_images():

    APP.list_of_files = {}
    APP.slugs = {}
    for (dirpath, _, filenames) in os.walk('static/images/pathology'):
        for filename in filenames:
            if filename.endswith('.vms'):
                APP.list_of_files[filename] = SlideImage(os.sep.join([dirpath, filename]))
                slug = filename.split(' ')[0]
                APP.slugs[slug] = filename


@APP.route('/static/image/<string:slug>')
def image(slug):

    try:
        filename = APP.slugs[slug]
        img = APP.list_of_files[filename]
    except KeyError:
        raise

    resp = {'dims': img.osr.dimensions, 'name' : slug, 'maxZoom' : img.zoom.level_count -1}

    return jsonify(resp)

@APP.route('/static/images/<string:slug>/<int:z>/<int:x>/<int:y>')
def tile(slug, z, x, y):

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

if __name__ == "__main__":

    APP.debug = True
    load_images()
    HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000
    APP.run(host='localhost', port=5000)
