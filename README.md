# Histology slide viewer

This software provides a whole slide image viewer. 
It is based on the [openslide-python](https://github.com/openslide/openslide-python) bindings  and [OpenSeadragon](https://github.com/openseadragon/openseadragon) tiled image viewer .


The viewer is available with an example image at (hdl-histology.northeurope.cloudapp.azure.com). It is possible to run the server locally using the provided Dockerfile, however, this does not include any example slides. The example slides has to be placed in the `static/images/pathology/` folder.