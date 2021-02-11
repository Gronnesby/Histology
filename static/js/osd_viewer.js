
var tiles;
var viewer;

function init_viewer(id, slug, height, width, size) {

    viewer = OpenSeadragon({
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
            tileSize: 254,
            tileOverlap: 2,
            getTileUrl: function(level, x, y) {
                return "/tile?slug=" + slug + "&level=" + level + "&x=" + x + "&y=" + y;
            }
        },
        success: function(item) {
            viewer.tiles = item.item;
        }
    });
}


function init_selection(viewer) {
    var selection = viewer.selection({
        allowRotation: false,
        onSelection: onSelectionConfirmed,
    })

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

function onSelectionConfirmed(viewer, rect) {

    
    //var url = new URL(window.location);
    var baseurl = window.location.protocol + '//' + window.location.host + '/annotate';
    
    var x = Math.floor(rect.x);
    var y = Math.floor(rect.y);
    var width = Math.floor(rect.width);
    var height = Math.floor(rect.height);
    var z = Math.floor(viewer.viewport.getZoom(true));


    var inferenceUrl = baseurl + "?slug=" + slug + "&x=" + x + "&y=" + y + "&w=" + width + "&h=" + height + "&level=" + z;
    

    fetch(inferenceUrl)
        .then(function(response){
            return response.blob();
        })
        .then(function(blob){

            // const viewportRect = self.viewer.viewport.imageToViewportRectangle(rect);
            // const webRect = self.viewer.viewport.viewportToViewerElementRectangle(viewportRect);
            // const { x, y, width, height } = webRect || {};
            // const { canvas } = self.viewer.drawer;
            // let source = canvas.toDataURL();

            // const img = new Image();
            // img.onload = function () {
                
            //     let ctx = croppedCanvas.getContext('2d');
            //     croppedCanvas.width = width;
            //     croppedCanvas.height = height;
            //     ctx.drawImage(img, x, y, width, height, 0, 0, width, height);
            //     let croppedSrc = croppedCanvas.toDataURL();

            //     //update viewer with cropped image
            //     self.tile = self.getTile(croppedSrc);
            //     self.ImageTileSource = new OpenSeadragon.ImageTileSource(self.tile);
            //     self.viewer.open(self.ImageTileSource);
            // }
            // img.src = source;

            const objectURL = URL.createObjectURL(blob);

            // create an image
            var overlayDiv = document.createElement('div');
            overlayDiv.id = "image-overlay";
            overlayDiv.className = "sd-overlay";
            
            var overlayImg = document.createElement('img');
            overlayImg.src = objectURL;
            overlayDiv.appendChild(overlayImg);
            var tilesource = viewer.world.getItemAt(0).source;
            var vp = viewer.tiles.imageToViewportRectangle(rect.x, rect.y, rect.width, rect.height);
            // var vp = viewer.viewport.imageToViewportRectangle(rect.x, rect.y, rect.width, rect.height);
            // alert(vp);

            var overlay = viewer.canvasOverlay({
                onRedraw: function() {
                    overlay.context2d().drawImage(overlayImg, vp.x, vp.y, vp.width, vp.height);
                },
                clearBeforeRedraw: true
            });
        })
        .catch(function(error) {
            // If there is any error you will catch them here
        });

}