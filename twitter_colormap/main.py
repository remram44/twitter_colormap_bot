if __name__ == '__main__':
    from twitter_colormap import main
    main()


import logging
from PIL import Image
import requests
from StringIO import StringIO
from twitter_colormap.identify import identify_colormap, JET, VIRIDIS
from twitter_colormap.twitter_stream import get_twitter_statuses, post


logger = logging.getLogger('twitter')


DUMP = False


def handle_status(status, images):
    viridis = jet = False

    for image_url in images:
        try:
            req = requests.get(image_url)
            if DUMP:
                if image_url.lower().endswith('.jpg'):
                    ext = 'jpg'
                else:
                    ext = 'png'
                fname = 'dumps/%s-%s.%s' % (
                    status.created_at.strftime('%Y%m%d_%H%M%S'),
                    status.author.screen_name,
                    ext)
                with open(fname, 'w') as fp:
                    fp.write(req.content)
            image = Image.open(StringIO(req.content))
        except Exception as e:
            logger.exception("Exception retrieving image: %s", image_url)
            continue

        try:
            colormap = identify_colormap(image)
        except Exception as e:
            logger.exception("Exception identifying image: %s", image_url)
            continue

        if colormap == VIRIDIS:
            viridis = True
        elif colormap == JET:
            jet = True

    if viridis:
        post("A plot using the new Viridis colormap. Great!",
             link=status)
    elif jet:
        post("You seem to be using the Jet colormap. Consider using Viridis "
             "(new in #matplotlib 2.0) "
             "http://matplotlib.org/style_changes.html#colormap",
             reply=status)


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    get_twitter_statuses(handle_status, track=['python', 'matplotlib', 'dataviz'])
