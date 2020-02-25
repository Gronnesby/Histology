
import os
import sys
import math
import PIL


from scipy.io import loadmat
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

    def get_image(self, coord, z, dim):

        level = (self.osr.level_count -1) - round(z/self.osr.level_count)
        level = max(0, min((self.osr.level_count-1), level))

        print("Level: {0} Z: {1} z/levelcount: {2}".format(level, z, z/self.osr.level_count))
        downsample = self.osr.level_downsamples[level]
        dim = (int(dim[0]/(downsample/2)), int(dim[1]/(downsample/2)))
        print("W, H: {0} X, Y: {1} Z: {2} level: {3} downsample: {4} level_count: {5}".format(dim, coord, z, level, downsample, self.osr.level_count))

        image = self.osr.read_region(coord, level, dim)
        return image


    def infer(self, coord, z, dim):
        
        # image = self.get_image(coord, z, dim)

        ## Inference code here
        mat = loadmat('postprocessing_inference.mat')['inst_map']
        
        return PIL.Image.fromarray(mat, mode="I")



if __name__ == "__main__":

    pass