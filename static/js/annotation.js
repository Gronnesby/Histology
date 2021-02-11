



async function onSelectionConfirmed(viewer, rect)
{

    var url = new URL(window.location);
    var path = window.location.pathname;
    var baseurl = window.location.protocol + '//' + window.location.host + '/annotate';

    var x = Math.floor(rect.x);
    var y = Math.floor(rect.y);
    var width = Math.floor(rect.width);
    var height = Math.floor(rect.height);
    var z = viewer.world.getItemAt(0).source.maxLevel;

    var vp = viewer.viewport.imageToViewportRectangle(rect.x, rect.y, rect.width, rect.height);

    var tiledImage = viewer.world.getItemAt(0);
    tiledImage.setCroppingPolygons([{"x": rect.x, "y": rect.y}, 
                                    {"x": rect.getBottomLeft().x, "y": rect.getBottomLeft().y}, 
                                    {"x": rect.getBottomRight().x, "y": rect.getBottomRight().y}, 
                                    {"x": rect.getTopRight().x, "y": rect.getTopRight().y},
                                    {"x": rect.x, "y": rect.y}]);
    viewer.forceRedraw();

    var elt = document.createElement("div");
    elt.id = "runtime-overlay";
    elt.className = "overlay";
    viewer.addOverlay({
        element: elt,
        location: new OpenSeadragon.Rect(vp.x, vp.y, vp.width, vp.height)
    });

    var slidename = path.substring(path.lastIndexOf('/') + 1);
    var annotateURL = baseurl + `/${slidename}/${z}/${x}_${y}/${width}_${height}`;

    fetch(annotateURL)
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
            viewer.forceRedraw();
        })
        .catch(function(error) {
            // If there is any error you will catch them here
        });
}