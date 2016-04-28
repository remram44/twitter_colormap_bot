import matplotlib.cm
import numpy
import logging
from sklearn.neighbors import KernelDensity


logger = logging.getLogger('twitter')


VIRIDIS = 'viridis'
JET = 'jet'


def test_array(colormap_name):
    colormap = matplotlib.cm.get_cmap(colormap_name)
    return colormap(numpy.linspace(0, 1, 100))[:, :3]


TEST_ARRAYS = {
    VIRIDIS: test_array('viridis'),
    JET: test_array('jet'),
}


def identify_colormap(image):
    image_obj = image
    image = numpy.asarray(image_obj, dtype=numpy.uint8)

    if image.shape[0] < 100 or image.shape[1] < 100:
        return None

    # Turn image into a 2D array (1D list of RGB triples)
    sh = image.shape
    assert len(sh) == 3
    assert sh[2] in (3, 4)
    logger.info("Got image %dx%d, classifying", image.shape[0], image.shape[1])
    flat = image.reshape(-1, sh[2])[:, :3] / 255.

    # subsample pixels
    state = numpy.random.RandomState(0)
    indices = state.choice(len(flat), size=min(len(flat), 2000), replace=False)
    # build kde estimate
    kde = KernelDensity(bandwidth=.1).fit(flat[indices])
    best_score = -numpy.inf
    scores = {}
    for colormap, array in TEST_ARRAYS.iteritems():
        score = kde.score(array)
        scores[colormap] = score
        if score > best_score:
            best_score = score
            best_colormap = colormap
    logger.info("Classification results: %s",
                ", ".join("%s: %.2f" % (name, scores[name])
                          for name in sorted(scores)))
    if best_score < -150:
        return None
    else:
        logger.info("Classified as %s", best_colormap)
        return best_colormap
