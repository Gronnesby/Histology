
var tiles;
var viewer;


function osd_init(tilesource, prefixUrl) {
    viewer = new OpenSeadragon({
        id: "view",
        tileSources: tilesource,
        prefixUrl: prefixUrl,
        showNavigator: true,
        showRotationControl: false,
        animationTime: 0.5,
        blendTime: 0.1,
        timeout: 12000,
    });
    
    viewer.addHandler("open", function() {
        // To improve load times, ignore the lowest-resolution Deep Zoom
        // levels.  This is a hack: we can't configure the minLevel via
        // OpenSeadragon configuration options when the viewer is created
        // from DZI XML.
        viewer.source.minLevel = 8;
    });

    viewer.selection({
        allowRotation: false,
        onSelection: function(rect) {
            annotateArea(viewer, rect)
        }
    });

    viewer.overlay_list = [];
    viewer.models_list = [];

}


function setLoc(viewer, x, y, w, h, z) {
    var r = new OpenSeadragon.Rect(x, y, w, h);
    viewer.viewport.fitBounds(r, true);
    console.dir(viewer.viewport.getBounds());
}
