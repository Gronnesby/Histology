

const viewer = OpenSeadragon({
    id: "map",
    prefixUrl: "static/images/",
    showNavigationControl: true,
    showNavigator: true,
    tileSources: {
        minLevel: 8,
        height: {{ imgheight }},
        width: {{ imgwidth }},
        tileSize: 256,
        getTileUrl: function( level, x, y )
        {
            return "/tile?slug=" + "{{ slug }}" + "&level=" + level + "&x=" + x + "&y=" + y;
            
        },
        overlays: [{
            id: 'image-ruler',
            x: 0.33, 
            y: 0.14, 
            width: 0.02, 
            height: 0.025,
            className: 'highlight'
        }]
    }
})

viewer.initializeAnnotations();