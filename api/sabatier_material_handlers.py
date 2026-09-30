from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.sabatier_schemas import (
    MaterialLikeIn,
    SabatierMaterialOut,
    SabatierMaterialPublishIn,
)
from data.sabatier_current_chemist import get_current_chemist_id
from data.sabatier_database import get_sabatier_session
from data.sabatier_minio import remove_material_file, upload_material_file
from data.sabatier_models import (
    DEFAULT_MATERIAL_IMAGE_NAME,
    DEFAULT_MATERIAL_VIDEO_NAME,
    MATERIAL_STATUS_DELETED,
    MATERIAL_STATUS_DRAFT,
    MATERIAL_STATUS_PUBLISHED,
    MaterialLike,
    SabatierMaterial,
)

router = APIRouter(prefix="/api/sabatier_materials", tags=["Материалы реакции"])


def liked_by_me(chemist_id: int):
    """Подзапрос: поставил ли текущий пользователь лайк этому материалу."""
    return (
        select(MaterialLike.id)
        .where(
            MaterialLike.material_id == SabatierMaterial.id,
            MaterialLike.chemist_id == chemist_id,
        )
        .exists()
    )


def material_query(chemist_id: int):
    return select(SabatierMaterial, liked_by_me(chemist_id))


def to_out(row, chemist_id: int) -> SabatierMaterialOut:
    material, is_liked = row
    out = SabatierMaterialOut.model_validate(material)
    out.is_mine = int(material.creator_chemist_id == chemist_id)
    out.is_liked = int(is_liked)
    return out


def load_material_row(session: Session, material_id: int, chemist_id: int):
    return session.execute(
        material_query(chemist_id).where(SabatierMaterial.id == material_id)
    ).first()


def store_material_file(upload_file, old_name: str, default_name: str) -> str:
    object_name = upload_material_file(upload_file)
    if old_name != default_name:
        remove_material_file(old_name)
    return object_name


def get_own_material(session: Session, material_id: int, chemist_id: int):
    return session.scalar(
        select(SabatierMaterial).where(
            SabatierMaterial.id == material_id,
            SabatierMaterial.creator_chemist_id == chemist_id,
            SabatierMaterial.material_status != MATERIAL_STATUS_DELETED,
        )
    )


def get_published_material(session: Session, chemist_id: int, material_id: int = None):
    query = material_query(chemist_id).where(
        SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED
    )
    if material_id is not None:
        query = query.where(SabatierMaterial.id == material_id)
    return session.execute(query.order_by(SabatierMaterial.id).limit(1)).first()


def get_next_material_id(session: Session, material_id: int):
    query = (
        select(SabatierMaterial.id)
        .where(SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED)
        .order_by(SabatierMaterial.id)
        .limit(1)
    )
    next_id = session.scalar(query.where(SabatierMaterial.id > material_id))
    return next_id if next_id is not None else session.scalar(query)


@router.get("", response_model=list[SabatierMaterialOut])
def get_sabatier_materials(
    min_reaction_value: int = Query(0, ge=0),
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    query = (
        material_query(chemist_id)
        .where(SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED)
        .order_by(SabatierMaterial.id)
    )
    if min_reaction_value > 0:
        query = query.where(SabatierMaterial.min_reaction_value >= min_reaction_value)

    return [to_out(row, chemist_id) for row in session.execute(query)]


@router.get("/draft", response_model=SabatierMaterialOut)
def get_sabatier_material_draft(session: Session = Depends(get_sabatier_session)):
    chemist_id = get_current_chemist_id()

    row = session.execute(
        material_query(chemist_id).where(
            SabatierMaterial.creator_chemist_id == chemist_id,
            SabatierMaterial.material_status == MATERIAL_STATUS_DRAFT,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_out(row, chemist_id)


@router.get("/feed", response_model=SabatierMaterialOut)
@router.get("/feed/{material_id}", response_model=SabatierMaterialOut)
def get_sabatier_material_feed(
    material_id: int = None,
    show_next: bool = Query(False, alias="next"),
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    if show_next and material_id is not None:
        material_id = get_next_material_id(session, material_id)
        if material_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    row = get_published_material(session, chemist_id, material_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_out(row, chemist_id)


@router.post("", response_model=SabatierMaterialOut, status_code=status.HTTP_201_CREATED)
def create_sabatier_material(
    material_name: str = Form(..., max_length=128),
    material_image: UploadFile | None = File(None),
    material_video: UploadFile | None = File(None),
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    draft_exists = session.scalar(
        select(SabatierMaterial.id).where(
            SabatierMaterial.creator_chemist_id == chemist_id,
            SabatierMaterial.material_status == MATERIAL_STATUS_DRAFT,
        )
    )
    if draft_exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    material = SabatierMaterial(
        material_name=material_name,
        material_status=MATERIAL_STATUS_DRAFT,
        material_image_name=(
            upload_material_file(material_image)
            if material_image is not None
            else DEFAULT_MATERIAL_IMAGE_NAME
        ),
        material_video_name=(
            upload_material_file(material_video)
            if material_video is not None
            else DEFAULT_MATERIAL_VIDEO_NAME
        ),
        creator_chemist_id=chemist_id,
        created_at=func.now(),
    )
    session.add(material)
    session.commit()
    return to_out(load_material_row(session, material.id, chemist_id), chemist_id)


@router.put("/{material_id}/image", response_model=SabatierMaterialOut)
def replace_sabatier_material_image(
    material_id: int,
    material_image: UploadFile = File(...),
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    material = get_own_material(session, material_id, chemist_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    material.material_image_name = store_material_file(
        material_image, material.material_image_name, DEFAULT_MATERIAL_IMAGE_NAME
    )
    session.commit()
    return to_out(load_material_row(session, material_id, chemist_id), chemist_id)


@router.put("/{material_id}/video", response_model=SabatierMaterialOut)
def replace_sabatier_material_video(
    material_id: int,
    material_video: UploadFile = File(...),
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    material = get_own_material(session, material_id, chemist_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    material.material_video_name = store_material_file(
        material_video, material.material_video_name, DEFAULT_MATERIAL_VIDEO_NAME
    )
    session.commit()
    return to_out(load_material_row(session, material_id, chemist_id), chemist_id)


@router.put("/{material_id}/publish", response_model=SabatierMaterialOut)
def publish_sabatier_material(
    material_id: int,
    payload: SabatierMaterialPublishIn,
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    material = session.scalar(
        select(SabatierMaterial).where(
            SabatierMaterial.id == material_id,
            SabatierMaterial.creator_chemist_id == chemist_id,
            SabatierMaterial.material_status == MATERIAL_STATUS_DRAFT,
        )
    )
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    material.material_description = payload.material_description
    material.min_reaction_value = payload.min_reaction_value
    material.molar_mass = payload.molar_mass
    material.material_status = MATERIAL_STATUS_PUBLISHED
    material.formed_at = func.now()
    session.commit()
    return to_out(load_material_row(session, material_id, chemist_id), chemist_id)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sabatier_material(
    material_id: int,
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    material = get_own_material(session, material_id, chemist_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    material.material_status = MATERIAL_STATUS_DELETED
    session.commit()


@router.post("/{material_id}/like", response_model=SabatierMaterialOut)
def like_sabatier_material(
    material_id: int,
    payload: MaterialLikeIn,
    session: Session = Depends(get_sabatier_session),
):
    chemist_id = get_current_chemist_id()

    if get_published_material(session, chemist_id, material_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    like = session.scalar(
        select(MaterialLike).where(
            MaterialLike.chemist_id == chemist_id,
            MaterialLike.material_id == material_id,
        )
    )
    if payload.liked == 1 and like is None:
        session.add(MaterialLike(chemist_id=chemist_id, material_id=material_id))
    elif payload.liked == 0 and like is not None:
        session.delete(like)
    session.commit()

    return to_out(load_material_row(session, material_id, chemist_id), chemist_id)
