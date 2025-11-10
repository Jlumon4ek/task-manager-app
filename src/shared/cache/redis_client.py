import logging
from typing import Optional, Union
import json
import redis
from django.conf import settings
from .interfaces import ICacheClient

logger = logging.getLogger(__name__)


class RedisClient(ICacheClient):
    _instance: Optional['RedisClient'] = None
    _connection: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._connection is None:
            self._connection = self._create_connection()
    
    @staticmethod
    def _create_connection() -> redis.Redis:
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )


    @property
    def client(self) -> redis.Redis:
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection
    

    def get(self, key: str) -> Optional[Union[str, dict, list]]:
        try:
            value = self.client.get(name=key)
            
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value  
                
        except redis.RedisError as e:
            logger.error(f"Error getting value from Redis for key '{key}': {e}")
            return None


    def set(
        self, 
        key: str, 
        value: Union[str, dict, list], 
        expiry: Optional[int] = None
    ) -> bool:

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            self.client.set(name=key, value=value, ex=expiry)
            logger.debug(f"Redis SET: {key} (TTL: {expiry}s)")
            return True
        except redis.RedisError as e:
            logger.error(f"Error setting value in Redis for key '{key}': {e}")
            return False
    

    def delete(self, key: str) -> bool:
        try:
            result = self.client.delete(key)
            logger.debug(f"Redis DELETE: {key} (result: {result})")
            return result == 1
        except redis.RedisError as e:
            logger.error(f"Error deleting value from Redis for key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) == 1
        except redis.RedisError as e:
            logger.error(f"Error checking existence in Redis for key '{key}': {e}")
            return False
    


    
