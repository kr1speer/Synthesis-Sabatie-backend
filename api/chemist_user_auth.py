from fastapi import Cookie, Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie
from sqlalchemy import select
from sqlalchemy.orm import Session

from data.sabatier_database import get_sabatier_session
from data.sabatier_models import ChemistUser
from data.sabatier_redis import SESSION_COOKIE_NAME, get_session_chemist_id

session_cookie_scheme = APIKeyCookie(
    name=SESSION_COOKIE_NAME,
    scheme_name="Сессия в куке",
    description="Идентификатор сессии из куки session_id, выдаёт POST /api/chemist_users/login",
    auto_error=False,
)


def load_session_chemist(
    session_id: str | None,
    session: Session,
) -> ChemistUser | None:
    """Пользователь по куке: берём ид сессии, в Redis находим ид пользователя, в БД — его самого."""
    if not session_id:
        return None

    chemist_id = get_session_chemist_id(session_id)
    if chemist_id is None:
        return None

    return session.scalar(select(ChemistUser).where(ChemistUser.id == chemist_id))


def get_current_chemist(
    session_id: str | None = Security(session_cookie_scheme),
    session: Session = Depends(get_sabatier_session),
) -> ChemistUser:
    """Методы создателя: без действующей сессии — 401."""
    chemist = load_session_chemist(session_id, session)
    if chemist is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return chemist


def get_optional_chemist_id(
    session_id: str | None = Cookie(None, alias=SESSION_COOKIE_NAME, include_in_schema=False),
    session: Session = Depends(get_sabatier_session),
) -> int | None:
    """Методы чтения: работают и для гостя, пользователь нужен лишь для is_mine и is_liked."""
    chemist = load_session_chemist(session_id, session)
    return chemist.id if chemist is not None else None
