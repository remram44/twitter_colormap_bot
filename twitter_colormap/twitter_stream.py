import logging
import tweepy


logger = logging.getLogger(__name__)


ACTUALLY_POST = False


SETTINGS = {}
execfile('twitter.txt', SETTINGS, SETTINGS)


auth = tweepy.OAuthHandler(SETTINGS['consumer_key'], SETTINGS['consumer_secret'])
auth.set_access_token(SETTINGS['access_token'], SETTINGS['access_secret'])
api = tweepy.API(auth)


class StreamListener(tweepy.StreamListener):
    def __init__(self, callback, **kwargs):
        super(StreamListener, self).__init__(**kwargs)
        self._callback = callback

    def on_status(self, status):
        if not hasattr(status, 'retweeted_status'):
            logger.debug("%s: %s",
                         status.author.screen_name, status.text)
            if hasattr(status, 'extended_entities'):
                images = [me['media_url']
                          for me in status.extended_entities['media']
                          if me['type'] == 'photo']
            else:
                images = []
            self._callback(status, images)

    def on_error(self, status_code):
        logger.error("error %d", status_code)
        return False


def get_twitter_statuses(callback, **kwargs):
    listener = StreamListener(callback=callback)
    stream = tweepy.Stream(auth=api.auth, listener=listener)
    stream.filter(**kwargs)


def status_link(status):
    return 'https://twitter.com/%s/status/%s' % (status.author.screen_name,
                                                 status.id)


def post(text, link=None, reply=None):
    if reply:
        text = "@%s %s" % (reply.author.screen_name, text)
    if ACTUALLY_POST:
        kwargs = {}
        if link:
            text = "%s %s" % (text, status_link(link))
        if reply:
            kwargs['in_reply_to_status_id'] = reply.id
        api.update_status(text, **kwargs)
    else:
        print()
        print("WOULD HAVE POSTED:")
        print(text)
        if link:
            print("linking %s" % status_link(link))
        if reply:
            print("in reply to %s" % status_link(reply))
        print()
