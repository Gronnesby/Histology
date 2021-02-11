import os
import re
import math
import timeit
import argparse
import json
import requests
import urllib

from tempfile import NamedTemporaryFile
from datetime import datetime
from collections import deque, defaultdict

import cv2
import numpy as np
from PIL import Image

from hover.src.scripts.viz_utils import visualize_instances
from hover.src.config import MODEL_PARAMETERS
import hover.src.scripts.process_utils as proc_utils


## for local
# from scripts.viz_utils import visualize_instances
# import scripts.process_utils as proc_utils


def timer(func, *args, **kwargs):
    start_time = timeit.default_timer()
    result = func(*args, **kwargs)
    elapsed = timeit.default_timer() - start_time
    print(f"Finished {func.__name__}. Time elapsed: {'{:.3f}'.format(elapsed)} sec")
    return result


class InfererURL:
    """
    Make sure that SERVER_URL is set up.

    input_img argument can be PIL image, numpy array or just path to .png file.
    """

    def __init__(self, input_img, model, server_url="", profile="", batch_size=15):
        self.server_url = (
            os.environ["SERVER_URL"] if "SERVER_URL" in os.environ else server_url
        )
        self.model_config = (
            os.environ["H_PROFILE"] if "H_PROFILE" in os.environ else profile
        )

        self.model = model
        self.endpoint = f"{self.server_url}:8501/v1/models/{self.model}:predict"

        
        try:
            requests.get(":".join(self.endpoint.split(":")[:-1])).ok is True
        except:
            raise
        
        assert self.model_config != ""

        data_config = MODEL_PARAMETERS[self.model_config]

        self.mask_shape = data_config["step_size"]
        self.input_shape = data_config["win_size"]
        self.nuclei_types = data_config["nuclei_types"]

        self.nr_types = len(self.nuclei_types.values()) + 1
        self.input_norm = True  # data_config['input_norm']
        self.remap_labels = False  # data_config['remap_labels']
        self.inf_batch_size = batch_size

        self.eval_inf_input_tensor_names = ["images:0"]
        self.eval_inf_output_tensor_names = ["predmap-coded:0"]

        self.colors = {
            "Inflammatory": (0.0, 255.0, 0.0),      # bright green
            "Dead cells": (255.0, 255.0, 0.0),      # bright yellow
            "Neoplastic cells": (255.0, 0.0, 0.0),  # red           # aka Epithelial malignant
            "Epithelial": (0.0, 0.0, 255.0),        # dark blue     # aka Epithelial healthy
            "Misc": (0.0, 0.0, 0.0),                # pure black    # aka 'garbage class'
            "Spindle": (0.0, 255.0, 255.0),         # cyan          # Fibroblast, Muscle and Endothelial cells
            "Connective": (0.0, 220.0, 220.0),      # darker cyan   # Connective plus Soft tissue cells
            "Background": (255.0, 0.0, 170.0),      # pink
            ###
            "light green": (170.0, 255.0, 0.0),     # light green
            "purple": (170.0, 0.0, 255.0),          # purple
            "orange": (255.0, 170.0, 0.0),          # orange
            "black": (32.0, 32.0, 32.0),            # black
        }
        
        self.color_mapping = {v: k for k, v in self.nuclei_types.items()}
        for key in self.color_mapping:
            self.color_mapping[key] = self.colors[self.color_mapping[key]]

        # if it is PIL image
        if isinstance(input_img, Image.Image):
            self.input_img = cv2.cvtColor(
                np.array(input_img, dtype=np.float32), cv2.COLOR_BGR2RGB
            )
        # if it is np array (f.eks. cv2 image)
        elif isinstance(input_img, np.ndarray):
            if isinstance(input_img.flat[0], np.uint8):
                self.input_img = cv2.cvtColor(
                    np.array(Image.fromarray(input_img, "RGB"), dtype=np.float32),
                    cv2.COLOR_BGR2RGB,
                )
            elif isinstance(input_img.flat[0], np.floating):
                self.input_img = cv2.cvtColor(np.float32(input_img), cv2.COLOR_BGR2RGB)
        # if it is filename
        elif os.path.isfile(input_img):
            self.input_img = cv2.cvtColor(cv2.imread(input_img), cv2.COLOR_BGR2RGB)
        else:
            raise Exception("Unsupported type of input image.")

    def __gen_prediction(self, x):

        step_size = self.mask_shape
        msk_size = self.mask_shape
        win_size = self.input_shape

        def get_last_steps(length, msk_size, step_size):
            nr_step = math.ceil((length - msk_size) / step_size)
            last_step = (nr_step + 1) * step_size
            return int(last_step), int(nr_step + 1)

        im_h = x.shape[0]
        im_w = x.shape[1]

        last_h, nr_step_h = get_last_steps(im_h, msk_size[0], step_size[0])
        last_w, nr_step_w = get_last_steps(im_w, msk_size[1], step_size[1])

        diff_h = win_size[0] - step_size[0]
        padt = diff_h // 2
        padb = last_h + win_size[0] - im_h

        diff_w = win_size[1] - step_size[1]
        padl = diff_w // 2
        padr = last_w + win_size[1] - im_w

        x = np.lib.pad(x, ((padt, padb), (padl, padr), (0, 0)), "reflect")

        sub_patches = []

        for row in range(0, last_h, step_size[0]):
            for col in range(0, last_w, step_size[1]):
                win = x[row : row + win_size[0], col : col + win_size[1]]
                sub_patches.append(win)

        pred_map = deque()

        while len(sub_patches) > self.inf_batch_size:
            mini_batch = sub_patches[: self.inf_batch_size]
            sub_patches = sub_patches[self.inf_batch_size :]
            mini_output = self.__predict_subpatch(mini_batch)
            mini_output = np.split(mini_output, self.inf_batch_size, axis=0)
            pred_map.extend(mini_output)
        if len(sub_patches) != 0:
            mini_output = self.__predict_subpatch(sub_patches)
            mini_output = np.split(mini_output, len(sub_patches), axis=0)
            pred_map.extend(mini_output)

        # Assemble back into full image
        output_patch_shape = np.squeeze(pred_map[0]).shape
        ch = 1 if len(output_patch_shape) == 2 else output_patch_shape[-1]

        # Assemble back into full image
        pred_map = np.squeeze(np.array(pred_map))
        pred_map = np.reshape(pred_map, (nr_step_h, nr_step_w) + pred_map.shape[1:])
        pred_map = (
            np.transpose(pred_map, [0, 2, 1, 3, 4])
            if ch != 1
            else np.transpose(pred_map, [0, 2, 1, 3])
        )
        pred_map = np.reshape(
            pred_map,
            (
                pred_map.shape[0] * pred_map.shape[1],
                pred_map.shape[2] * pred_map.shape[3],
                ch,
            ),
        )
        pred_map = np.squeeze(pred_map[:im_h, :im_w])  # just crop back to original size

        return pred_map

    def __process_instance(self, pred_map, output_dtype="uint16"):
        """
        Post processing script for image tiles

        Args:
            pred_map: commbined output of nc, np and hv branches
            output_dtype: data type of output

        Returns:
            pred_inst:     pixel-wise nuclear instance segmentation prediction
            pred_type_out: pixel-wise nuclear type prediction
        """

        # pred = np.squeeze(pred_map['result'])

        pred_inst = pred_map[..., self.nr_types :]
        pred_type = pred_map[..., : self.nr_types]

        pred_inst = np.squeeze(pred_inst)
        pred_type = np.argmax(pred_type, axis=-1)
        pred_type = np.squeeze(pred_type)

        pred_inst = proc_utils.proc_np_hv(pred_inst)

        if self.remap_labels:
            pred_inst = proc_utils.remap_label(pred_inst, by_size=True)

        pred_type_out = np.zeros([pred_type.shape[0], pred_type.shape[1]])
        # * Get class of each instance id, stored at index id-1
        pred_id_list = list(np.unique(pred_inst))[1:]  # exclude background ID
        pred_inst_type = np.full(len(pred_id_list), 0, dtype=np.int32)
        for idx, inst_id in enumerate(pred_id_list):
            inst_tmp = pred_inst == inst_id
            inst_type = pred_type[pred_inst == inst_id]
            type_list, type_pixels = np.unique(inst_type, return_counts=True)
            type_list = list(zip(type_list, type_pixels))
            type_list = sorted(type_list, key=lambda x: x[1], reverse=True)
            inst_type = type_list[0][0]
            if inst_type == 0:  # ! pick the 2nd most dominant if exist
                if len(type_list) > 1:
                    inst_type = type_list[1][0]
            pred_type_out += inst_tmp * inst_type
        pred_type_out = pred_type_out.astype(output_dtype)
        pred_inst = pred_inst.astype(output_dtype)

        return pred_inst, pred_type_out
        # pred = {'inst_map': pred_inst,
        #         'type_map': pred_type,
        #         'inst_type': pred_inst_type[:, None],
        #         'inst_centroid': pred_inst_centroid}
        # overlaid_output = visualize_instances(pred_inst, image, (self.nr_types, pred_inst_type[:, None])) #cfg.nr_types + 1
        # overlaid_output = cv2.cvtColor(overlaid_output, cv2.COLOR_BGR2RGB)

        # with open(os.path.join(proc_dir, f'{basename}.log'), 'w') as log_file:
        #     unique, counts = np.unique(pred_inst_type[:, None], return_counts=True)
        #     print(f'{basename} : {dict(zip(unique, counts))}', file = log_file)

    def __predict_subpatch(self, subpatch):
        """
        subpatch : numpy.ndarray
        inputs - outputs
        instances - predictions
        """
        response = requests.post(
            self.endpoint, data=json.dumps({"inputs": np.array(subpatch).tolist()})
        )
        return np.array(response.json()["outputs"])  # [0]

    def run_save(self, save_dir=None, only_contours=False, logging=False):

        assert save_dir is not None

        temp_file = NamedTemporaryFile()
        name_out = os.path.join(save_dir, os.path.split(temp_file.name)[1])

        # pred_map = {'result': [self.__gen_prediction(self.input_img)]} # {'result':[pred_map]}
        # np.save(f"{name_out}_map.npy", pred_map)

        pred_map = self.__gen_prediction(self.input_img)
        pred_inst, pred_type = self.__process_instance(pred_map)

        if only_contours:
            pred_inst = np.expand_dims(pred_inst, -1)
            pred_inst[pred_inst > 0] = 1
            np.save(f"{name_out}.npy", pred_inst)
            if logging:
                print(
                    f"Saved countours only (all cells) to <{name_out}.npy>. {datetime.now().strftime('%H:%M:%S')}"
                )
            return

        overlaid_output = visualize_instances(
            self.input_img, self.color_mapping, pred_inst, pred_type
        )
        overlaid_output = cv2.cvtColor(overlaid_output, cv2.COLOR_BGR2RGB)
        cv2.imwrite(f"{name_out}.png", overlaid_output)
        if logging:
            print(
                f"Saved processed image to <{name_out}.png>. {datetime.now().strftime('%H:%M:%S')}"
            )  # '%H:%M:%S.%f'

        # combine instance and type arrays for saving
        pred_inst = np.expand_dims(pred_inst, -1)
        pred_type = np.expand_dims(pred_type, -1)
        pred = np.dstack([pred_inst, pred_type])

        np.save(f"{name_out}.npy", pred)
        if logging:
            print(
                f"Saved pred to <{name_out}.npy>. {datetime.now().strftime('%H:%M:%S')}"
            )

    def run(self):
        pred_map = self.__gen_prediction(self.input_img)
        pred_inst, _ = self.__process_instance(pred_map)
        pred_inst = np.expand_dims(pred_inst, -1)
        pred_inst[pred_inst > 0] = 1
        return pred_inst

    def run_type(self, type_nuclei=None):
        pred_map = self.__gen_prediction(self.input_img)
        _, pred_type = self.__process_instance(pred_map)
        pred_type = np.expand_dims(pred_type, -1)

        if type_nuclei is not None:
            assert type_nuclei in self.nuclei_types.keys()
            pred_nuclei = pred_type
            pred_nuclei[pred_nuclei != self.nuclei_types[type_nuclei]] = 0
            pred_nuclei[pred_nuclei == self.nuclei_types[type_nuclei]] = 1
            return pred_nuclei
        else:
            return pred_type

def get_available_models(server_url, port=8502):
    url = urllib.parse.urlparse(f"{server_url}:{port}/config").geturl()
    response = requests.get(url)
    models = []
    for model in re.findall(r"name: '\w*'", response.text):
        models.append(model.split(": ")[1].strip("'"))
    return models


if __name__ == "__main__":
    """
    Example: 
        H_PROFILE=hv_consep \
        SERVER_URL=http://localhost \
        python external_infer_url.py --input_img '/data/input/data_consep/data/test/Images/test_1.png' --save_dir '/data/output/'

        or

        H_PROFILE=hv_pannuke \
        SERVER_URL=http://localhost \
        python external_infer_url.py --input_img '/data/input/data_consep/data/test/Images/test_1.png'

        or

        result = InfererURL(PILimage, 'consep_aug', server_url='http://localhost', profile="hv_consep").run()

    """
    parser = argparse.ArgumentParser()
    # parser.add_argument('--gpu', help='Comma separated list of GPU(s) to use.', default="0")
    parser.add_argument("--input_img", help="Full path to input image")
    parser.add_argument("--save_dir", help="Path to the directory to save result")
    args = parser.parse_args()
    ### InfererURL(input_img, model, server_url="", profile="", batch_size=15)
    ### Models (check via <get_available_models>): consep_aug, consep_original, pannuke_aug, pannuke_original

    inferer = InfererURL(args.input_img, 'consep_aug', server_url='http://localhost', profile="hv_consep")

    ### to save predictions use 'run_save'
    # inferer.run_save(save_dir=args.save_dir)

    ### get segmentation masks
    # result = timer(inferer.run)

    ### get specific nuclei type, if type_nuclei='Inflammatory' - returns mask with several classes [0, len(self.nuclei_types)]
    # result = timer(inferer.run_type, type_nuclei='Inflammatory')

    ### get available models on tf-serving
    # get_available_models('http://localhost')
