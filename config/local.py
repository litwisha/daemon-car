from .base import BaseConfig


class LocalConfig(
    BaseConfig,
):
    REDIS_PARAMS = {
        'decode_responses': True,
    }
