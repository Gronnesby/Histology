
var map = L.map('map', {minZoom: 1, zoomControl: false, zoomSnap: 0, setMaxZoom: 7});
var tilelayer;

var freedraw = new FreeDraw({
        mode: FreeDraw.NONE
    });

var stateChangingButton = L.easyButton({
    states: [{
            stateName: 'paint',        // name the state
            icon:      'fa-paint-brush',               // and define its properties
            title:     'Draw on the image',      // like its title
            onClick: function(btn) {       // and its callback
                freedraw.mode((FreeDraw.CREATE | FreeDraw.DELETE));
                btn.state('navigate');    // change state on click!
            }
        }, {
            stateName: 'navigate',
            icon:      'fa-hand-grab-o',
            title:     'Navigate the image',
            onClick: function(btn) {
                freedraw.mode(FreeDraw.NONE);
                btn.state('paint');
            }
    }]
});

stateChangingButton.addTo(map);

function set_image(selector)
{
    map.eachLayer(function(layer){
        map.removeLayer(layer);
    });
    var image = 'Snitt25NZHE40';
    var url = '/static/image/' + image;
    var request = new XMLHttpRequest();

    request.onreadystatechange = function()
    {
        if (request.readyState == 4 && request.status == 200)
        {
            load_image(request.responseText, image);
        }
    };
    request.open('GET', url);
    request.send();
    
    map.addLayer(freedraw);

}

function load_image(responseText)
{
    var resp = JSON.parse(responseText);
    var dim = resp.dims;

    map.setView(new L.LatLng(0,0), 0);

    L.tileLayer('static/images/' + resp.name + '/{z}/{x}/{y}', { 
        noWrap: true,
        minZoom: 12,
        maxZoom: resp.maxZoom
    }).addTo(map);
    map.invalidateSize();
    
    var southWest = map.unproject([1, dim[1]], map.getMaxZoom()),
        northEast = map.unproject([dim[0], 1], map.getMaxZoom()),
        bounds = new L.LatLngBounds(southWest, northEast);
    // Restrict to bounds
    map.setMaxBounds(bounds);
    map.fitBounds(bounds);
}

var legend = L.control({position: 'topright'});
legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    div.innerHTML = '<select onchange="set_image(this)"> \
                     <option value="Snitt25">Snitt25</option> \
                     <option value="Snitt26">Snitt26</option> \
                     <option value="Snitt27">Snitt27</option> \
                     </select>';
    div.firstChild.onmousedown = div.firstChild.ondblclick = L.DomEvent.stopPropagation;
    return div;
};
legend.addTo(map);

window.onload(set_image({value : "sample"}));