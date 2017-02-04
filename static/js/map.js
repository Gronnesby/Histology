
var img = [13466, 8467];
var map = L.map('map', {minZoom: 0, zoomControl: false, zoomSnap: 0});
var rc = new L.RasterCoords(map, img);

// set max zoom Level (might be `x` if gdal2tiles was called with `-z 0-x` option)
map.setMaxZoom(6);
map.options.minZoom = 2;

// all coordinates need to be unprojected using the `unproject` method
// set the view in the lower right edge of the image
map.setView(rc.unproject([img[0] / 2, img[1] / 2]), 3);

// the tile layer containing the image generated with `gdal2tiles --leaflet -p raster -w none <img> tiles`
L.tileLayer('./static/images/tiles/{z}/{x}/{y}.png', {
  noWrap: true
}).addTo(map);

var freedraw = new FreeDraw({
    mode: FreeDraw.CREATE | FreeDraw.DELETE
});
map.addLayer(freedraw);


