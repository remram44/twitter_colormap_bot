import matplotlib.cm
import numpy
import logging
import scipy.ndimage


BINS = 16
DISTANCE = 4


logger = logging.getLogger('twitter')


VIRIDIS = 'viridis'
JET = 'jet'


def test_array(colormap_name):
    colormap = matplotlib.cm.get_cmap(colormap_name)

    # These are all the colors in the colormap
    colors = colormap(numpy.arange(0.0, 1.0, 0.001))
    colors = (colors * 255.0).astype(numpy.uint8)

    hist, _ = numpy.histogramdd(colors[:, :3], bins=BINS, range=[(0, 256)] * 3,
                                normed=False)

    convo = numpy.ones((DISTANCE * 2,) * 3, dtype=numpy.int)

    # Reject everything (-4)
    testarray = -4 * numpy.ones((BINS,) * 3, dtype=numpy.int)

    # Recognize the colors (set them to +1)
    recog = scipy.ndimage.filters.convolve(hist, convo, mode='constant',
                                           origin=(0, 0, 0))
    recog = recog != 0
    testarray += recog * 5

    # Ignore white (set to 0)
    testarray[-DISTANCE:, -DISTANCE:, -DISTANCE:] = 0

    return testarray


TEST_ARRAYS = {
    VIRIDIS: test_array('viridis'),
    JET: test_array('jet'),
}

def identify_colormap(image_obj):
    if image_obj.mode not in ('RGB', 'RGBA'):
        image_obj = image_obj.convert('RGBA')
    image = numpy.asarray(image_obj, dtype=numpy.uint8)

    if image.shape[0] < 100 or image.shape[1] < 100:
        return None

    # Turn image into a 2D array (1D list of RGB triples)
    sh = image.shape
    assert len(sh) == 3
    assert sh[2] in (3, 4)
    logger.info("Got image %dx%d, classifying", image.shape[0], image.shape[1])
    image = image.reshape(sh[0] * sh[1], sh[2])[:, :3]

    # Get 3D histogram
    # It gives the frequency of each color (RGB triple) in a bin
    histogram, _ = numpy.histogramdd(image, bins=BINS, range=[(0, 256)] * 3)
    histogram /= image.shape[0]

    # Test if it's a heatmap
    max_bins = numpy.sort(histogram.flatten())[::-1]
    if (#(max_bins > 0.008).sum() < 10 or  # Less than 10 different colors
            numpy.sum(max_bins[:6]) > 0.85):
        logger.info("Doesn't look like a heatmap -- %d colors, sum = %.4f",
                (max_bins > 0.005).sum(), numpy.sum(max_bins[:6]))
        return None

    # Check for colormaps
    results = {}
    for name, testarray in TEST_ARRAYS.iteritems():
        results[name] = numpy.dot(testarray.flatten(), histogram.flatten())

    logger.info("Classification results: %s",
                ", ".join("%s: %.2f" % (name, results[name])
                          for name in sorted(results)))
    nb = sum(1 for res in results.itervalues() if res > 0.0)
    if nb == 1:
        result = [name for name, res in results.iteritems() if res > 0.0][0]
        logger.info("Classified as %s", result)
        return result
    elif nb > 1:
        logger.warning("Multiple colormaps were identified!")
        return None
    else:
        logger.info("No colormap found")
        return None
