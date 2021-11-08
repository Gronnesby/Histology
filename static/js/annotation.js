



async function annotateArea(viewer, rect)
{

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

    model_selector = document.getElementById("model-selection")
    model = model_selector.options[model_selector.selectedIndex].text
    var annotateURL = baseurl + `/${slidename}/${z}/${x}_${y}/${width}_${height}/${model}`;

    fetch(annotateURL)
        .then(function(response){
            return response.blob();
        })
        .then(function(blob){

            const objectURL = URL.createObjectURL(blob);

            var overlayDiv = document.createElement('div');
            overlayDiv.id = "div-overlay";
            overlayDiv.className = "div-overlay";
            
            var img = document.createElement('img');
            img.id = "img-overlay";
            img.src = objectURL;
            overlayDiv.appendChild(img);

            viewer.addOverlay({
                element: overlayDiv,
                location: new OpenSeadragon.Rect(vp.x, vp.y, vp.width, vp.height),
                checkResize: true
            });
            
            viewer.removeOverlay(elt);
            viewer.forceRedraw();
            viewer.overlay_list.push(overlayDiv);
        })
        .catch(function(error) {
            alert(error);
        });
}
