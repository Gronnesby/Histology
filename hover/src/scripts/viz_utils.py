import cv2
import numpy as np
import itertools


def bounding_box(img):
    rows = np.any(img, axis=1)
    cols = np.any(img, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    # due to python indexing, need to add 1 to max
    # else accessing will be 1px in the box, not out
    rmax += 1
    cmax += 1
    return [rmin, rmax, cmin, cmax]


def normalize(mask, dtype=np.uint8):
    return (255 * mask / np.amax(mask)).astype(dtype)


def visualize_instances(
    input_image, color_dict, predict_instance, predict_type=None, line_thickness=2
):
    """
    Overlays segmentation results on image as contours
    Args:
        input_image: input image
        predict_instance: instance mask with unique value for every object
        predict_type: type mask with unique value for every class
        line_thickness: line thickness of contours
    Returns:
        overlay: output image with segmentation overlay as contours
    """

    overlay = np.copy((input_image).astype(np.uint8))

    if predict_type is not None:
        type_list = list(np.unique(predict_type))  # get list of types
        type_list.remove(0)  # remove background
    else:
        type_list = [4]  # yellow

    for iter_type in type_list:
        if predict_type is not None:
            label_map = (predict_type == iter_type) * predict_instance
        else:
            label_map = predict_instance
        instances_list = list(np.unique(label_map))  # get list of instances
        instances_list.remove(0)  # remove background
        contours = []
        for inst_id in instances_list:
            instance_map = np.array(
                predict_instance == inst_id, np.uint8
            )  # get single object
            y1, y2, x1, x2 = bounding_box(instance_map)
            y1 = y1 - 2 if y1 - 2 >= 0 else y1
            x1 = x1 - 2 if x1 - 2 >= 0 else x1
            x2 = x2 + 2 if x2 + 2 <= predict_instance.shape[1] - 1 else x2
            y2 = y2 + 2 if y2 + 2 <= predict_instance.shape[0] - 1 else y2
            inst_map_crop = instance_map[y1:y2, x1:x2]
            contours_crop = cv2.findContours(
                inst_map_crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            index_correction = np.asarray([[[[x1, y1]]]])
            for i in range(len(contours_crop[0])):
                contours.append(
                    list(
                        np.asarray(contours_crop[0][i].astype("int32"))
                        + index_correction
                    )
                )
        contours = list(itertools.chain(*contours))

        cv2.drawContours(
            overlay, np.asarray(contours), -1, color_dict[iter_type], line_thickness
        )
    return overlay
