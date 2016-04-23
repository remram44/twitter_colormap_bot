import matplotlib.cm
import numpy
import logging
import scipy.ndimage


BINS = 64
DISTANCE = 4


logger = logging.getLogger('twitter')


VIRIDIS = 'viridis'
JET = 'jet'


# Construct the bins
edges = numpy.repeat(
    (numpy.arange(BINS + 1, dtype=numpy.uint8) * 256 / BINS)
        .reshape((1, BINS + 1)),
    3,
    axis=0)


def test_array(colormap_name):
    colormap = matplotlib.cm.get_cmap(colormap_name)

    # These are all the colors in the colormap
    colors = colormap(numpy.arange(0.0, 1.0, 0.001))
    colors = (colors * 255.0).astype(numpy.uint8)

    hist, _ = numpy.histogramdd(colors[:, :3], bins=edges, normed=False)

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


def identify_colormap(image):
    image_obj = image
    image = numpy.asarray(image_obj, dtype=numpy.uint8)

    # Turn image into a 2D array (1D list of RGB triples)
    sh = image.shape
    assert len(sh) == 3
    assert sh[2] in (3, 4)
    logger.info("Got image %dx%d, classifying", image.shape[0], image.shape[1])
    image = image.reshape(sh[0] * sh[1], sh[2])[:, :3]

    # Get 3D histogram
    # It gives the frequency of each color (RGB triple) in a bin
    histogram, _ = numpy.histogramdd(image, bins=edges)
    histogram /= image.shape[0]

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
