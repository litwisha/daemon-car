from redis import StrictRedis

class BaseConfig:

    redis_client = StrictRedis(decode_responses=True)
