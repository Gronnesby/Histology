



async function annotateArea(viewer, rect)
{

    var path = window.location.pathname;
    var baseurl = window.location.protocol + '//' + window.location.host;

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
    var annotateURL = baseurl + '/annotate' + `/${slidename}/${z}/${x}_${y}/${width}_${height}/${model}`;

    const r = fetch(annotateURL)
        .then((response) => response.text())
        .then((resp) =>{
            alert(resp);
            return resp;
        });
    
    var id = await r;
    var metaURL = baseurl + `/overlay/false/${id}`

    const m = fetch(metaURL)
        .then((response) => response.json())
        .then((resp) =>{
            return resp
        });

    var meta = await m;

    var imageURL = baseurl + `/overlay/true/${id}`
    
    fetch(imageURL)
        .then(function(response){
            return response.blob();
        })
        .then(function(blob){

            const objectURL = URL.createObjectURL(blob);
            
            var overlayDiv = document.createElement('div');
            overlayDiv.id = "div-overlay";
            overlayDiv.className = "div-overlay";

            var infoText = document.createElement('div');
            infoText.id = "div-infobox"
            infoText.className = "div-infobox";

            var ul = document.createElement('ul');
            for (let k in meta) {
                var li = document.createElement('li');
                li.innerHTML = k + " : " + meta[k];
                li.style.color = 'white';
                ul.appendChild(li);
            }
            
            ul.style.width = "100%";
            infoText.appendChild(ul);

            var img = document.createElement('img');
            img.id = "img-overlay";
            img.src = objectURL;


            overlayDiv.appendChild(img);
            overlayDiv.appendChild(infoText);

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
