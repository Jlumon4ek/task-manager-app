from shared.email.factory import EmailClientFactory
from shared.email.interfaces import IEmailClient

email_client: IEmailClient = EmailClientFactory.get_client()

__all__ = [
    'IEmailClient',
    'EmailClientFactory',
    'email_client',
]