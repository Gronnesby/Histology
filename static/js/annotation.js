



async function annotateArea(selection, rect)
{

    var viewer = selection.viewer;
    var path = window.location.pathname;
    var baseurl = window.location.protocol + '//' + window.location.host;

    var x = Math.floor(rect.x);
    var y = Math.floor(rect.y);
    var width = Math.floor(rect.width);
    var height = Math.floor(rect.height);
    var z = viewer.world.getItemAt(0).source.maxLevel;

    var vp = viewer.viewport.imageToViewportRectangle(rect.x, rect.y, rect.width, rect.height);

    if (((rect.width * rect.height) > 250000) && ((rect.width * rect.height) < 1960000)) {
        let largeImage = confirm("Selection exceeds the recommended size of 1000x1000 pixels.\n This may take several minutes to complete, continue?");
        if (!largeImage) {
            return;
        }
    } else if ((rect.width * rect.height) > 1960000) {
        alert("Selection is too large\n");
        return;
    }
    
    var elt = document.createElement("div");
    elt.id = "runtime-placeholder";
    elt.className = "overlay";
    viewer.addOverlay({
        element: elt,
        location: new OpenSeadragon.Rect(vp.x, vp.y, vp.width, vp.height)
    });
    
    viewer.forceRedraw();


    selection.disable();
    var slidename = path.substring(path.lastIndexOf('/') + 1);

    model_selector = document.getElementById("model-selection");
    model = model_selector.options[model_selector.selectedIndex].text;
    var annotateURL = baseurl + '/annotate' + `/${slidename}/${z}/${x}_${y}/${width}_${height}/${model}`;
    
    fetch(annotateURL)
        .then((response) => response.json())
        .then(function(data) {

            // Create a div to contain the overlay
            var overlayDiv = document.createElement('div');
            overlayDiv.id = "div-overlay";
            overlayDiv.className = "div-overlay";

            // Info box with colored cell counts
            var infoText = document.createElement('div');
            infoText.id = "div-infobox"
            infoText.className = "div-infobox";

            // Populate the info box
            meta = data["meta"];
            var ul = document.createElement('ul');
            for (let k in meta) {
                var li = document.createElement('li');
                li.innerHTML = k + " : " + meta[k][0];
                li.style.color = `rgb(${meta[k][1][0]}, ${meta[k][1][1]}, ${meta[k][1][2]})`;
                ul.appendChild(li);
            }

            ul.style.width = "max-content";
            infoText.appendChild(ul);

            // Create the overlay image
            var img = new Image();
            img.id = "img-overlay";
            img.src = data["img"];

            // Append the elements to the overlay div
            overlayDiv.appendChild(img);
            overlayDiv.appendChild(infoText);

            // Set up handlers for hovering
            overlayDiv.onmouseenter = function(){
                infoText.style.visibility = 'visible';
            };

            overlayDiv.onmouseleave = function(){
                infoText.style.visibility = 'hidden';
            }
            
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
