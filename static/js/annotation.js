



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
    
    var elt = document.createElement("div");
    elt.id = "runtime-placeholder";
    elt.className = "overlay";
    viewer.addOverlay({
        element: elt,
        location: new OpenSeadragon.Rect(vp.x, vp.y, vp.width, vp.height)
    });
    
    viewer.forceRedraw();
    var slidename = path.substring(path.lastIndexOf('/') + 1);
    var annotateURL = baseurl + `/${slidename}/${z}/${x}_${y}/${width}_${height}`;

    fetch(annotateURL)
        .then(function(response){
            return response.blob();
        })
        .then(function(blob){

            const objectURL = URL.createObjectURL(blob);
            // const viewportRect = viewer.viewport.imageToViewportRectangle(rect);
            // const webRect = viewer.viewport.viewportToViewerElementRectangle(viewportRect);
            // const { x, y, width, height } = webRect || {};
            // const { canvas } = viewer.drawer;

            var img = document.createElement('img');
            img.id = "img-overlay";
            img.src = objectURL;
            viewer.addOverlay({
                element: img,
                location: new OpenSeadragon.Rect(vp.x, vp.y, vp.width, vp.height)
            });
            
            viewer.removeOverlay(elt);
            viewer.forceRedraw();
            viewer.overlay_list.push(img);
        })
        .catch(function(error) {
            alert(error);
        });
}