from fastapi import APIRouter, Depends, HTTPException, Response, Security, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.chemist_user_auth import session_cookie_scheme
from api.sabatier_schemas import ChemistUserLoginIn, ChemistUserOut, ChemistUserRegisterIn
from data.sabatier_database import get_sabatier_session
from data.sabatier_models import ChemistUser
from data.sabatier_redis import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    create_session,
    delete_session,
)

router = APIRouter(prefix="/api/chemist_users", tags=["Инженеры-технологи"])


@router.post(
    "/register",
    response_model=ChemistUserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация инженера-технолога",
    description=(
        "Создаёт нового пользователя по логину, паролю и ФИО. Признак модератора "
        "с клиента не принимается: новый пользователь всегда обычный создатель. "
        "Пароль в ответе не возвращается. Сессия при регистрации не создаётся — "
        "после неё нужна аутентификация."
    ),
    responses={
        201: {"description": "Пользователь создан"},
        409: {"description": "Логин уже занят"},
    },
)
def register_chemist_user(
    payload: ChemistUserRegisterIn,
    session: Session = Depends(get_sabatier_session),
):
    login_taken = session.scalar(
        select(ChemistUser.id).where(ChemistUser.chemist_login == payload.chemist_login)
    )
    if login_taken is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    chemist = ChemistUser(
        chemist_login=payload.chemist_login,
        chemist_password=payload.chemist_password,
        full_name=payload.full_name,
        is_moderator=False,
    )
    session.add(chemist)
    session.commit()
    session.refresh(chemist)
    return chemist


@router.post(
    "/login",
    response_model=ChemistUserOut,
    summary="Аутентификация",
    description=(
        "Проверяет логин и пароль по таблице пользователей. При успехе создаёт сессию "
        "в Redis (хеш `session:<ид сессии>` с ид и логином пользователя, время жизни "
        f"{SESSION_TTL_SECONDS} секунд) и отдаёт её идентификатор в заголовке "
        f"`Set-Cookie: {SESSION_COOKIE_NAME}=...`. В теле ответа — признак модератора, "
        "по которому фронтенд меняет представление приложения."
    ),
    responses={
        200: {"description": "Сессия создана, идентификатор отдан в куке"},
        401: {"description": "Неверный логин или пароль"},
    },
)
def login_chemist_user(
    payload: ChemistUserLoginIn,
    response: Response,
    session: Session = Depends(get_sabatier_session),
):
    chemist = session.scalar(
        select(ChemistUser).where(
            ChemistUser.chemist_login == payload.chemist_login,
            ChemistUser.chemist_password == payload.chemist_password,
        )
    )
    if chemist is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session_id = create_session(chemist.id, chemist.chemist_login, chemist.is_moderator)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return chemist


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Деавторизация",
    description=(
        "Удаляет сессию из Redis и гасит куку в браузере. Требует действующей сессии: "
        "без неё — 401."
    ),
    responses={
        204: {"description": "Сессия удалена"},
        401: {"description": "Сессии нет"},
    },
)
def logout_chemist_user(
    response: Response,
    session_id: str | None = Security(session_cookie_scheme),
):
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    delete_session(session_id)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
