


function init_viewer(id, slug, height, width) {

    var viewer = OpenSeadragon({
        id: id,
        showNavigationControl: true,
        showNavigator: true,
        maxZoomPixelRatio: 100,
        prefixUrl: "static/images/",
        tileSources: {
            minLevel: 8,
            height: height,
            width: width,
            tileSize: 256,
            getTileUrl: function(level, x, y){
                return "/tile?slug=" + slug + "&level=" + level + "&x=" + x + "&y=" + y;
            }
        },
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

    var rect = viewer.viewport.imageToViewportRectangle(result);
    var bb = rect.getBoundingBox();
    console.dir(r);

    var url = new URL(window.location);
    var baseurl = window.location.protocol + '//' + window.location.host + window.location.pathname;
    var slug = url.searchParams.get("slug");
    viewer.viewport.fitBounds(bb);
    var r = viewer.viewport.getBounds();

    alert(baseurl + "?slug=" + slug + "&x=" + r.x.toFixed(4) + "&y=" + r.y.toFixed(4) + "&w=" + r.width.toFixed(4) + "&h=" + r.height.toFixed(4));
}

// function non_primary_press_handler (event) {

//     var viewer = event.userData;
//     var webpoint = event.position;

//     var viewcoords = viewer.viewport.pointFromPixel(webpoint);
//     var zoom = Math.floor(viewer.viewport.getZoom());
//     viewer.viewport.panTo(viewcoords, false);
//     viewer.viewport.zoomTo(zoom + 1);

//     viewer.addOverlay({
//         element: "map",
//         location: new OpenSeadragon.Rect(webpoint[0], webpoint[1], 0.02, 0.025)
//     });
    
// }


// function non_primary_release_handler (event) {
    
//     var viewer = event.userData;
//     var webpoint = event.position;

//     var viewcoords = viewer.viewport.pointFromPixel(webpoint);
//     var imagecoords = viewer.viewport.viewportToImageCoordinates(viewcoords);

//     alert("Imagecoords:" + imagecoords);
// }