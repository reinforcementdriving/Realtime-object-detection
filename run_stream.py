import logging
import time
import sys
import os
import yaml
import numpy as np

from lib.mpfps import FPS

"""
Execute ssd_mobilenet_v1, ssd_mobilenet_v2, ssdlite_mobilenet_v2, ssd_inception_v2_coco
Repository:
https://github.com/naisy/realtime_object_detection

About repogitory: Forked from GustavZ's github.
https://github.com/GustavZ/realtime_object_detection

Updates:
- Add parallel detection for Mask R-CNN.
- Remove split from Mask R-CNN.
- Support DeepLab V3 models. `model_type: deeplab_v3`

- Add image input.
- Rename config.yml parameter name from save_to_movie to save_to_file.

- Support Faster R-CNN
- support ssd_mobilenet_v1 11 Jun, 2017 model.
- Add save_to_movie.
- Support MASK R-CNN
- Support ssd_mobilenet_v2, ssdlite_mobilenet_v2, ssd_inception_v2_coco

- Add Multi-Processing visualization. : Detection and visualization are asynchronous.

- Drop unused files.

- Parallel run to complete JIT. : Improve startup time from 90sec to 78sec.
- Add time details.             : To understand the processing time well.

- Separate split and non-split code.     : Remove unused session from split code.
- Remove Session from load frozen graph. : Reduction of memory usage.

- Flexible sleep_interval.          : Maybe speed up on high spec PC.
- FPS separate to multi-processing. : Speed up.
- FPS streaming calculation.        : Flat fps.
- FPS is average of fps_interval.   : Flat fps. (in fps_stream)
- FPS updates every 0.2 sec.        : Flat fps. (in fps_snapshot)

- solve: Multiple session cannot launch problem. tensorflow.python.framework.errors_impl.InternalError: Failed to create session.
"""

def load_config():
    """
    LOAD CONFIG FILE
    Convert config.yml to DICT.
    """
    cfg = None
    if (os.path.isfile('config.yml')):
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
    else:
        raise FileNotFoundError(("File not found: config.yml"))
    cfg.update({'src_from': 'camera'})
    return cfg

def log_format(debug_mode):
    """
    LOG FORMAT
    If debug_mode, show detailed log
    """
    if debug_mode:
        np.set_printoptions(precision=5, suppress=True, threshold=np.inf)  # suppress scientific float notation
        logging.basicConfig(level=logging.DEBUG,
                            format='[%(levelname)s] time:%(created).8f pid:%(process)d pn:%(processName)-10s tid:%(thread)d tn:%(threadName)-10s fn:%(funcName)-10s %(message)s',
        )
    return

def download_model():
    """
    Download Model form TF's Model Zoo
    """
    model_file = model_name + '.tar.gz'
    download_base = 'http://download.tensorflow.org/models/object_detection/'
    if not os.path.isfile(model_path):
        print('Model not found. Downloading it now.')
        opener = urllib.request.URLopener()
        opener.retrieve(download_base + model_file, model_file)
        tar_file = tarfile.open(model_file)
        for file in tar_file.getmembers():
            file_name = os.path.basename(file.name)
            if 'frozen_inference_graph.pb' in file_name:
                tar_file.extract(file, os.getcwd() + '/models/')
        os.remove(os.getcwd() + '/' + model_file)
    else:
        print('Model found. Proceed.')

def main():
    try:
        """
        LOAD SETUP VARIABLES
        """
        cfg = load_config()
        debug_mode = cfg['debug_mode']
        model_type = cfg['model_type']

        """
        LOG FORMAT MODE
        """
        log_format(debug_mode)

        """
        START DETECTION, FPS, FPS PRINT
        """
        fps = FPS(cfg)
        fps_counter_proc = fps.start_counter()
        fps_console_proc = fps.start_console()
        if model_type == 'nms_v0':
            from lib.detection_nms_v0 import NMSV0
            detection = NMSV0()
            detection.start(cfg)
        elif model_type == 'nms_v1':
            from lib.detection_nms_v1 import NMSV1
            detection = NMSV1()
            detection.start(cfg)
        elif model_type == 'nms_v2':
            from lib.detection_nms_v2 import NMSV2
            detection = NMSV2()
            detection.start(cfg)
        elif model_type == 'trt_v1':
            from lib.detection_trt_v1 import TRTV1
            detection = TRTV1()
            detection.start(cfg)
        elif model_type == 'mask_v1':
            from lib.mtdetection_mask_v1 import MASKV1
            detection = MASKV1()
            detection.start(cfg)
        elif model_type == 'faster_v2':
            from lib.detection_faster_v2 import FasterV2
            detection = FasterV2()
            detection.start(cfg)
        elif model_type == 'deeplab_v3':
            from lib.detection_deeplab_v3 import DeepLabV3
            detection = DeepLabV3()
            detection.start(cfg)
        else:
            raise IOError(("Unknown model_type."))
        fps_counter_proc.join()
        fps_console_proc.join()
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        pass

if __name__ == '__main__':
    main()

