
import os
import sys
import math
import PIL
import io

from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator


class SlideImage(object):
    DOWNSAMPLE_FACTOR = 4
    TILE_SIZE = 254

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

        self.zoom = DeepZoomGenerator(self.osr, tile_size=self.TILE_SIZE, limit_bounds=True)
        print("File {0} \nDimensions (Level 0) {1}\n".format(self.filename, self.osr.dimensions))
        print("DeepZoom properties:\nLevel count: {0}\nLevel Dimensions:{1}\n".format(self.zoom.level_count, self.zoom.level_dimensions))
        

    def get_image_size(self):

        return self.osr.dimensions

    def get_tile(self, z, coord):
        
        image = self.zoom.get_tile(z, coord)
        return image

    def get_image(self, coord, z, dim):

        # level = (self.osr.level_count -1) - round(z/self.osr.level_count)
        # level = max(0, min((self.osr.level_count-1), level))
        # downsample = self.osr.level_downsamples[level]

        downsample = self.DOWNSAMPLE_FACTOR
        level = self.osr.get_best_level_for_downsample(downsample)

        print("Level: {0} Z: {1} z/levelcount: {2}".format(level, z, z/self.osr.level_count))
        print("W, H: {0} X, Y: {1} Z: {2} level: {3} downsample: {4} level_count: {5}".format(dim, coord, z, level, downsample, self.osr.level_count))

        dim = (int(dim[0]/downsample), int(dim[1]/downsample))
        image = self.osr.read_region(coord, level, dim)
        return image


    def infer(self, coord, z, dim):
        
        img = self.get_image(coord, z, dim)
        

        ## Inference code here
        ## Should be something like model.predict(img)
        ## img should be a python PIL image, and it expects the same as output.
        img = img.convert(mode="RGB")
        img.name = self.filename
        

        # img = PIL.Image.fromarray(img, mode="P")
        # img.putalpha(img.convert(mode="L"))

        return img




if __name__ == "__main__":

    pass
