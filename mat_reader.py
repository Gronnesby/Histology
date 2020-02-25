
import PIL

from scipy.io import loadmat
import matplotlib.pyplot as plt


def plot_postprocessed(data):

    print(data)
    data = data['inst_map']
    data = PIL.Image.fromarray(data, mode='I')

    plt.subplot(1, 2, 1)
    plt.imshow(data)
    plt.xlabel('Postprocessed output')

def plot_raw(data):

    data = data['result'][0,:,:,0]
    plt.subplot(1, 2, 2)
    plt.imshow(data)
    plt.xlabel('Raw output')


if __name__ == "__main__":

    plot_postprocessed(loadmat('postprocessing_inference.mat'))
    plot_raw(loadmat('output_inference.mat'))
    plt.tight_layout()
    plt.show()


