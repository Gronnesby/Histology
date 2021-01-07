import os



def create_thumbnail(path):

    try:
        im = Image.open(path)
        im.thumbnail(THUMBNAIL_SIZE)
        outfile = imagefile.replace("_map2.jpg", "_thumbnail.jpg")
        im.save(os.path.join(os.path.dirpath(path), outfile), "JPEG")
    except IOError:
        print("cannot create thumbnail for", imagefile)
