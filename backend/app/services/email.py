from email.message import EmailMessage

import aiosmtplib

from ..core.config import Settings


class EmailService:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def send_login_code(self, recipient: str, code: str) -> None:
        message = EmailMessage()
        message['From'] = self._settings.smtp_from
        message['To'] = recipient
        message['Subject'] = 'Ваш код для входа в VibeCode IDE'
        message.set_content(
            f'''
Привет!

Твой код для входа: {code}
Он действует 10 минут. Введи его в IDE, чтобы подтвердить e-mail.

— Команда VibeCode
'''.strip()
        )

        await aiosmtplib.send(
            message,
            hostname=self._settings.smtp_host,
            port=self._settings.smtp_port,
            start_tls=self._settings.smtp_tls,
            username=self._settings.smtp_user or None,
            password=self._settings.smtp_password or None,
        )


