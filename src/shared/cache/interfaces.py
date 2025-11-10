from abc import ABC, abstractmethod

class ICacheClient(ABC):
    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(self, key: str, value, expiry: int = None):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass


    
