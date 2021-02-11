
MODEL_PARAMETERS = {
    "hv_consep":
    {
        "step_size": [80, 80],
        "win_size": [270, 270],
        "nuclei_types":
        {
            "Misc": 1,
            "Inflammatory": 2,
            "Epithelial": 3,
            "Spindle": 4,
        }

    },

    "hv_pannuke":
    {
        "step_size": [164, 164],
        "win_size": [256, 256],
        "nuclei_types":
        {
            "Inflammatory": 1,
            "Connective": 2,
            "Dead cells": 3,
            "Epithelial": 4,
            "Neoplastic cells": 5
        }
    }
}