import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.security import create_access_token
from ..database import get_session
from ..schemas import AuthCodeRequest, AuthCodeVerify, AuthSuccessResponse
from ..services.auth import generate_code, store_code, upsert_user, verify_code
from ..services.email import EmailService


router = APIRouter(prefix='/auth', tags=['auth'])
logger = logging.getLogger(__name__)


@router.post('/request-code', status_code=status.HTTP_202_ACCEPTED)
async def request_code(
    payload: AuthCodeRequest,
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()
    user = await upsert_user(session, payload.email, payload.full_name)
    code = generate_code()
    await store_code(session, user, code)
    await session.commit()

    email_service = EmailService(settings)

    async def fire_and_forget():
        try:
            await email_service.send_login_code(payload.email, code)
        except Exception as exc:  # noqa: BLE001
            logger.error('Failed to send login code: %s', exc)

    asyncio.create_task(fire_and_forget())
    return {'detail': 'Code sent'}


@router.post('/verify', response_model=AuthSuccessResponse)
async def verify(
    payload: AuthCodeVerify,
    session: AsyncSession = Depends(get_session),
):
    user = await verify_code(session, payload.email, payload.code)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid code')
    await session.commit()

    token = create_access_token(str(user.id))
    return AuthSuccessResponse(access_token=token, user=user)


