



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
    var annotateURL = baseurl + `/${slidename}/${z}/${x}_${y}/${width}_${height}`;

    fetch(annotateURL)
        .then(function(response){
            return response.blob();
        })
        .then(function(blob){

            const objectURL = URL.createObjectURL(blob);

            var overlayDiv = document.createElement('div');
            overlayDiv.id = "div-overlay";
            overlayDiv.className = "overlay";
            
            var img = document.createElement('img');
            img.id = "img-overlay";
            img.src = objectURL;
            overlayDiv.appendChild(img)

            viewer.addOverlay({
                element: img,
                location: new OpenSeadragon.Rect(vp.x, vp.y, vp.width, vp.height),
                checkResize: false
            });
            
            viewer.removeOverlay(elt);
            viewer.forceRedraw();
            viewer.overlay_list.push(overlayDiv);
        })
        .catch(function(error) {
            alert(error);
        });
}



// function onSelectionConfirmed(viewer, rect) {

    
//     //var url = new URL(window.location);
//     var baseurl = window.location.protocol + '//' + window.location.host + '/annotate';
    
//     var x = Math.floor(rect.x);
//     var y = Math.floor(rect.y);
//     var width = Math.floor(rect.width);
//     var height = Math.floor(rect.height);
//     var z = Math.floor(viewer.viewport.getZoom(true));


//     var inferenceUrl = baseurl + "?slug=" + slug + "&x=" + x + "&y=" + y + "&w=" + width + "&h=" + height + "&level=" + z;
    

//     fetch(inferenceUrl)
//         .then(function(response){
//             return response.blob();
//         })
//         .then(function(blob){

//             const objectURL = URL.createObjectURL(blob);

//             // create an image

//             var overlayImg = document.createElement('img');
//             overlayImg.className = "image-overlay";
//             overlayImg.src = objectURL;
//             //overlayDiv.appendChild(overlayImg);

//             var tilesource = viewer.world.getItemAt(0).source;
//             var vp = viewer.tiles.imageToViewportRectangle(rect.x, rect.y, rect.width, rect.height);

//             overlay.element().appendChild(document.querySelector('.text-overlay'));

//             var imageOverlay = document.querySelector('.image-overlay');
//             overlay.element().appendChild(overlayImg);
//             overlay.onClick(overlayImg, function() {
//                 alert('Hello!');
//             });

//             // var overlay = viewer.canvasOverlay({
//             //     onRedraw: function() {
//             //         overlay.context2d().drawImage(overlayImg, vp.x, vp.y, vp.width, vp.height);
//             //     },
//             //     clearBeforeRedraw: true
//             // });
//         })
//         .catch(function(error) {
//             // If there is any error you will catch them here
//         });

// }