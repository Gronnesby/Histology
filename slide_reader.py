
from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator


class SlideImage(object):
    def __init__(self, filename):
        self.filename = filename

        try:
            self.osr = OpenSlide(self.filename)
        except OpenSlideUnsupportedFormatError:
            print 'Format of file {0} is not supported by openslide'.format(self.filename)
            raise
        except OpenSlideError:
            print 'Unknown Openslide error'
            raise

        self.zoom = DeepZoomGenerator(self.osr, tile_size=254, limit_bounds=True)
        print 'Tiles in image: {0}'.format(self.zoom.tile_count)
        print 'Tile levels: {0}'.format(self.zoom.level_count)
        print 'Tile dimensions: {0}'.format(self.zoom.level_dimensions)

    def get_image_size(self):

        return self.osr.dimensions

    def get_tile(self, z, coord):

        image = self.zoom.get_tile(z, coord)
        return image


if __name__ == "__main__":

    osr = SlideImage("./static/images/pathology/Snitt25NZHE40 - 2017-02-02 12.58.50.vms")
    print osr.get_image_size()
    osr.get_tile(11, (0, 0)).show()
