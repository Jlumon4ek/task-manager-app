from typing import List
from .interfaces import IEmailClient


class FakeEmailClient(IEmailClient):
    def __init__(self):
        pass

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        print(f"[FAKE EMAIL] To: {to_address}")
        print(f"[FAKE EMAIL] Subject: {subject}")
        print(f"[FAKE EMAIL] Body: {body}")
        print("-" * 80)

    def send_bulk_email(self, to_addresses: List[str], subject: str, body: str) -> None:
        for address in to_addresses:
            self.send_email(address, subject, body)

