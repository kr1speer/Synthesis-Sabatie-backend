from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.sabatier_schemas import ChemistUserLoginIn, ChemistUserOut, ChemistUserRegisterIn
from data.sabatier_database import get_sabatier_session
from data.sabatier_models import ChemistUser

router = APIRouter(prefix="/api/chemist_users", tags=["Инженеры-технологи"])


@router.post("/register", response_model=ChemistUserOut, status_code=status.HTTP_201_CREATED)
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


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
def login_chemist_user(payload: ChemistUserLoginIn):
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_chemist_user():
    return Response(status_code=status.HTTP_204_NO_CONTENT)
