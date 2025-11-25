from fastapi import APIRouter, Depends

from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas import DashboardSnapshot, UserRead


router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get('/me/dashboard', response_model=DashboardSnapshot)
async def dashboard(current_user: User = Depends(get_current_user)):
    return DashboardSnapshot(
        last_executor_status='idle',
        pending_jobs=2,
        last_language='typescript',
        recent_actions=[
            f'User {current_user.email} requested Docker run',
            'Lint checks passed',
            'Queued submission #142',
        ],
    )

