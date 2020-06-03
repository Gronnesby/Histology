
from config import *
from heimmune.imageprocess import ImageProcess
from heimmune.configuration import Configuration



def geometric_analysis(image):

    conf = Configuration()
    return ImageProcess(conf).get_immune_cells(image)




