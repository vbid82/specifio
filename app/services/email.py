import httpx
import asyncio
import logging
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_magic_link_email(to_email: str, first_name: str, token: str) -> bool:
    magic_link_url = f"{settings.magic_link_base_url}?token={token}"

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <p>Hello {first_name},</p>
            <p>Click below to access Specifio.</p>
            <div style="margin: 30px 0;">
                <a href="{magic_link_url}" style="display: inline-block; background-color: #000; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-weight: 500;">Sign In to Specifio</a>
            </div>
            <p style="font-size: 14px; color: #666;">This link expires in 1 hour.</p>
            <p style="font-size: 12px; color: #999; margin-top: 40px;">If you did not request this, ignore this email.</p>
        </div>
    </body>
    </html>
    """

    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": "Sign in to Specifio",
        "html": html_body,
    }

    async def attempt():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
            )
            return response.status_code < 300

    try:
        success = await attempt()
        if not success:
            await asyncio.sleep(0.5)
            success = await attempt()
        if not success:
            logger.error(f"Failed to send magic link email to {to_email}")
        return success
    except Exception as e:
        logger.error(f"Error sending magic link email to {to_email}: {e}")
        return False
