
import os
import sys
from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator

class SlideImage(object):
    def __init__(self, filename):
        self.filename = filename

        try:
            self.osr = OpenSlide(self.filename)
        except OpenSlideUnsupportedFormatError:
            print('Format of file {0} is not supported by openslide'.format(self.filename))
            raise
        except OpenSlideError:
            print('Unknown Openslide error')
            raise

        self.zoom = DeepZoomGenerator(self.osr, tile_size=256, limit_bounds=True)
        print(self.zoom)

    def get_image_size(self):

        return self.osr.dimensions

    def get_tile(self, z, coord):

        image = self.zoom.get_tile(z, coord)
        return image

    def save(self, dzi_path):
        pre, _ = os.path.splitext(self.filename)
        dzi_file = os.path.join(pre, ".dzi")
        self.zoom.save(os.path.join(dzi_path, dzi_file))
