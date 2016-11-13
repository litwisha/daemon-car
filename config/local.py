from .base import BaseConfig


class LocalConfig(
    BaseConfig,
):
    REDIS_PARAMS = {
        'decode_responses': True,
    }

    PHANTOMJS_PATH = '/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs'
