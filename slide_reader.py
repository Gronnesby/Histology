
import os
import sys
import math
import PIL
import io
import cProfile
import matplotlib.pyplot as plt

from openslide import OpenSlide, OpenSlideUnsupportedFormatError, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator

from config import DEEPZOOM_TILE_OVERLAP, DEEPZOOM_TILE_SIZE, DEEPZOOM_DOWNSAMPLE_FACTOR



class SlideImage(object):

    

    def __init__(self, filename, downsample=DEEPZOOM_DOWNSAMPLE_FACTOR):
        self.filename = filename
        self.downsample = downsample

        try:
            self.osr = OpenSlide(self.filename)
        except OpenSlideUnsupportedFormatError:
            print('Format of file {0} is not supported by openslide'.format(self.filename))
            raise
        except OpenSlideError:
            print('Unknown Openslide error')
            raise

        self.zoom = DeepZoomGenerator(self.osr, tile_size=DEEPZOOM_TILE_SIZE, limit_bounds=False)
        print("File {0} \nDimensions (Level 0) {1}\n".format(self.filename, self.osr.dimensions))
        print("DeepZoom properties:\nLevel count: {0}\nLevel Dimensions:{1}\n".format(self.zoom.level_count, self.zoom.level_dimensions))
        
    def set_downsample(self, ds):
        self.downsample = ds

    def get_image_size(self):

        return self.osr.dimensions

    def get_tile(self, z, coord):
        
        image = self.zoom.get_tile(z, coord)
        return image

    def get_image(self, coord, z, dim):

        # level = (self.osr.level_count -1) - round(z/self.osr.level_count)
        # level = max(0, min((self.osr.level_count-1), level))
        # downsample = self.osr.level_downsamples[level]

        level = self.osr.get_best_level_for_downsample(self.downsample)

        print("Level: {0} Z: {1} z/levelcount: {2}".format(level, z, z/self.osr.level_count))
        print("W, H: {0} X, Y: {1} Z: {2} level: {3} downsample: {4} level_count: {5}".format(dim, coord, z, level, self.downsample, self.osr.level_count))

        dim = (int(dim[0]/self.downsample), int(dim[1]/self.downsample))
        image = self.osr.read_region(coord, level, dim)
        return image


    def infer(self, coord, z, dim):
        
        img = self.get_image(coord, z, dim)
        
        ## Inference code here
        ## Should be something like model.predict(img)
        ## img should be a python PIL image, and it expects the same as output.
        img = img.convert(mode="RGB")
        img.name = self.filename
        
        #infer = InfererURL(img, 'http://hovernet.northeurope.azurecontainer.io:8501/v1/models/hover_pannuke:predict', 'hv_seg_class_pannuke')
        #overlay = infer.run()
        #overlay = overlay[:, :, 0]

        # overlay = PIL.Image.fromarray(overlay, mode="P")
        # img.putalpha(img.convert(mode="L"))

        #plt.imshow(img)
        #plt.imshow(overlay, alpha=0.5)

        #plt.show()

        return img


    def benchmark(self):
        coord = (50371, 50357)
        z = 20
        dim = (5500, 4000)

        self.set_downsample(8)
        self.infer(coord, z, dim)


if __name__ == "__main__":

    s = SlideImage('static/images/pathology/Snitt25NZHE40 - 2017-02-02 12.58.50.vms')

    # cProfile.run('s.benchmark()', sort='cumtime')

    s.benchmark()


        
