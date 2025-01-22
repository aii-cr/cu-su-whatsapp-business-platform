import smtplib
from email.message import EmailMessage
from app.config import settings

async def send_password_recovery_email(email: str, token: str):
    """Envía un correo electrónico para la recuperación de contraseña."""
    msg = EmailMessage()
    msg.set_content(f"Para restablecer tu contraseña, haz clic en el siguiente enlace: {settings.DOMAIN}/reset-password/{token}")
    msg["Subject"] = "Recuperación de contraseña"
    msg["From"] = settings.SMTP_SENDER_EMAIL
    msg["To"] = email

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_SENDER_EMAIL, settings.SMTP_SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Correo enviado a {email}")
        
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
