rm -rf static/tiles
python gdal2tiles-leaflet/gdal2tiles-multiprocess.py --leaflet -p raster -w none $1 $2
