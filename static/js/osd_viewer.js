
var tiles;

function init_viewer(id, slug, height, width) {

    var viewer = OpenSeadragon({
        id: id,
        showNavigationControl: true,
        showNavigator: true,
        maxZoomPixelRatio: 100,
        prefixUrl: "static/images/"
    });

    viewer.addTiledImage({
        tileSource: {
            minLevel: 8,
            height: height,
            width: width,
            tileSize: 256,
            getTileUrl: function(level, x, y) {
                return "/tile?slug=" + slug + "&level=" + level + "&x=" + x + "&y=" + y;
            }
        },
        success: function(item) {
            viewer.tiles = item.item;
        }
    });

    return viewer;
}


function init_selection(viewer) {
    var selection = viewer.selection({
        allowRotation: false
    })

    selection.addEventListener

    return selection
}

function init_tracker (id, viewer) {

    var tracker = new OpenSeadragon.MouseTracker({
        element: id,
        userData: viewer,
        restrictToImage: true
    });

    return tracker;
}


function setLoc(viewer, x, y, w, h, z) {
    var r = new OpenSeadragon.Rect(x, y, w, h);
        
    viewer.viewport.fitBounds(r, true);
    console.dir(viewer.viewport.getBounds());
}

function onSelectionConfirmed(result) {

    tiles = viewer.tiles;

    var rect = viewer.viewport.imageToViewportRectangle(result);
    var bb = rect.getBoundingBox();

    var url = new URL(window.location);
    var baseurl = window.location.protocol + '//' + window.location.host + '/annotate';
    var slug = url.searchParams.get("slug");
    viewer.viewport.fitBounds(bb);

    var ir = tiles.viewportToImageRectangle(viewer.viewport.getBounds());
    var x = Math.floor(ir.x);
    var y = Math.floor(ir.y);
    var width = Math.floor(ir.width);
    var height = Math.floor(ir.height);
    var z = Math.floor(viewer.viewport.getZoom(true));

    var inferenceUrl = baseurl + "?slug=" + slug + "&x=" + x + "&y=" + y + "&w=" + width + "&h=" + height + "&level=" + z;

    fetch(inferenceUrl)
        .then(function(response){
            return response.blob();
        })
        .then(function(blob){

            const objectURL = URL.createObjectURL(blob);

            // create an image
            var overlayDiv = document.createElement('div');
            overlayDiv.id = "annotation-overlay";
            overlayDiv.className = "highlight";
            
            var overlayImg = document.createElement('img');
            overlayImg.src = objectURL;
            
            overlayDiv.appendChild(overlayImg);

            viewer.addOverlay({
                element: overlayDiv,
                location: OpenSeadragon.Rect(x, y, width, height)
            });
        })
        .catch(function(error) {
            // If there is any error you will catch them here
        });

}