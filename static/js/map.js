
var img = [13466, 8467]
var map = L.map('map', {drawControl: true, minZoom: 0})
var rc = new L.RasterCoords(map, img)
// set max zoom Level (might be `x` if gdal2tiles was called with `-z 0-x` option)
map.setMaxZoom(rc.zoomLevel())
// all coordinates need to be unprojected using the `unproject` method
// set the view in the lower right edge of the image
map.setView(rc.unproject([img[0] / 2, img[1] / 2]), 3)

// the tile layer containing the image generated with `gdal2tiles --leaflet -p raster -w none <img> tiles`
L.tileLayer('./static/images/tiles/{z}/{x}/{y}.png', {
  noWrap: true
}).addTo(map)

var MyCustomMarker = L.Icon.extend({
    options: {
        shadowUrl: null,
        iconAnchor: new L.Point(12, 12),
        iconSize: new L.Point(24, 24),
        iconUrl: './static/css/images/marker-icon.png'
    }
});


var editableLayers = new L.FeatureGroup();
map.addLayer(editableLayers);

var options = {
    position: 'topright',
    draw: {
        polyline: {
            shapeOptions: {
                color: '#2C7CFF',
                weight: 10
            }
        },
        polygon: {
            allowIntersection: false, // Restricts shapes to simple polygons
            drawError: {
                color: '#e1e100', // Color the shape will turn when intersects
                message: '<strong>Oh snap!<strong> you can\'t draw that!' // Message that will show when intersect
            },
            shapeOptions: {
                color: '#2C7CFF'
            }
        },
        circle: false, // Turns off this drawing tool
        rectangle: {
            shapeOptions: {
                clickable: false
            }
        },
        marker: {
            icon: new MyCustomMarker()
        }
    },
    edit: {
        featureGroup: editableLayers, //REQUIRED!!
        remove: false
    }
};

var drawControl = new L.Control.Draw(options);
map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function (e) {
    var type = e.layerType,
        layer = e.layer;

    if (type === 'marker') {
        layer.bindPopup('');
    }

    editableLayers.addLayer(layer);
});
