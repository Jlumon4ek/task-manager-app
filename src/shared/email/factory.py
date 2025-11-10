from django.conf import settings
from shared.email.interfaces import IEmailClient



class EmailClientFactory:
    @staticmethod
    def create_client(backend: str = None) -> IEmailClient:
        backend = backend or getattr(settings, 'EMAIL_BACKEND', 'fake')
        if backend == 'fake':
            from shared.email.fake_client import FakeEmailClient
            return FakeEmailClient()
        
        raise ValueError(f"Unsupported email backend: {backend}")
