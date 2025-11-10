from abc import ABC, abstractmethod
from typing import List


class IEmailClient(ABC):
    @abstractmethod
    def send_email(self, to_address: str, subject: str, body: str) -> None:
        pass
    
    @abstractmethod
    def send_bulk_email(self, to_addresses: List[str], subject: str, body: str) -> None:
        pass
