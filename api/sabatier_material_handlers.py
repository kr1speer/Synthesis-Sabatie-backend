from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from api.chemist_user_auth import get_current_chemist, get_optional_chemist_id
from api.sabatier_schemas import (
    MaterialLikeIn,
    SabatierMaterialOut,
    SabatierMaterialPublishIn,
)
from data.sabatier_database import get_sabatier_session
from data.sabatier_minio import upload_material_file
from data.sabatier_models import (
    DEFAULT_MATERIAL_IMAGE_NAME,
    DEFAULT_MATERIAL_VIDEO_NAME,
    MATERIAL_STATUS_DELETED,
    MATERIAL_STATUS_DRAFT,
    MATERIAL_STATUS_PUBLISHED,
    ChemistUser,
    MaterialLike,
    SabatierMaterial,
)

router = APIRouter(prefix="/api/sabatier_materials", tags=["Материалы реакции"])


def liked_by_me(chemist_id: int | None):
    if chemist_id is None:
        return literal(False)

    return (
        select(MaterialLike.id)
        .where(
            MaterialLike.material_id == SabatierMaterial.id,
            MaterialLike.chemist_id == chemist_id,
        )
        .exists()
    )


def material_query(chemist_id: int | None):
    return select(SabatierMaterial, liked_by_me(chemist_id))


def to_out(row, chemist_id: int | None) -> SabatierMaterialOut:
    material, is_liked = row
    out = SabatierMaterialOut.model_validate(material)
    out.is_mine = int(material.creator_chemist_id == chemist_id)
    out.is_liked = int(is_liked)
    return out


def load_material_row(session: Session, material_id: int, chemist_id: int | None):
    return session.execute(
        material_query(chemist_id).where(SabatierMaterial.id == material_id)
    ).first()


def get_own_material(session: Session, material_id: int, chemist_id: int):
    """Материал для изменения: 404 если его нет, 403 если он чужой — авторизация по создателю."""
    material = session.scalar(
        select(SabatierMaterial).where(
            SabatierMaterial.id == material_id,
            SabatierMaterial.material_status != MATERIAL_STATUS_DELETED,
        )
    )
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if material.creator_chemist_id != chemist_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return material


def get_published_material(session: Session, chemist_id: int | None, material_id: int = None):
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


@router.get(
    "",
    response_model=list[SabatierMaterialOut],
    summary="Список материалов с фильтрацией",
    description=(
        "Только опубликованные материалы, удалённые наружу не передаются. Фильтр "
        "`min_reaction_value` выполняется в SQL-запросе на бэкенде. Метод чтения: "
        "доступен и гостю, и создателю. Для гостя `is_mine` и `is_liked` всегда 0, "
        "для авторизованного пользователя считаются по его сессии."
    ),
    responses={200: {"description": "Список опубликованных материалов"}},
)
def get_sabatier_materials(
    min_reaction_value: int = Query(
        0, ge=0, description="минимальная масса вещества для типовой реакции, г"
    ),
    chemist_id: int | None = Depends(get_optional_chemist_id),
    session: Session = Depends(get_sabatier_session),
):
    query = (
        material_query(chemist_id)
        .where(SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED)
        .order_by(SabatierMaterial.id)
    )
    if min_reaction_value > 0:
        query = query.where(SabatierMaterial.min_reaction_value >= min_reaction_value)

    return [to_out(row, chemist_id) for row in session.execute(query)]


@router.get(
    "/draft",
    response_model=SabatierMaterialOut,
    summary="Черновик текущего пользователя",
    description=(
        "Черновик пользователя из сессии, ид не указывается: черновик не более одного. "
        "Описание и оба поля по предметной области у него ещё `null` — их заполняет "
        "публикация. Метод создателя: гостю — 401."
    ),
    responses={
        200: {"description": "Черновик пользователя"},
        401: {"description": "Пользователь не аутентифицирован"},
        404: {"description": "У пользователя нет черновика"},
    },
)
def get_sabatier_material_draft(
    chemist: ChemistUser = Depends(get_current_chemist),
    session: Session = Depends(get_sabatier_session),
):
    row = session.execute(
        material_query(chemist.id).where(
            SabatierMaterial.creator_chemist_id == chemist.id,
            SabatierMaterial.material_status == MATERIAL_STATUS_DRAFT,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_out(row, chemist.id)


@router.get(
    "/feed",
    response_model=SabatierMaterialOut,
    summary="Лента материалов",
    description=(
        "Из БД читается ровно одна строка. Без `material_id` отдаёт первый "
        "опубликованный материал, с `material_id` — указанный, а вместе с "
        "`next=true` — следующий опубликованный за ним. Следующий ищет СУБД: ид "
        "могут идти с пропусками, за последним материалом лента возвращается "
        "к первому. Метод чтения, доступен и гостю."
    ),
    responses={
        200: {"description": "Один материал ленты"},
        404: {"description": "Такого опубликованного материала нет"},
    },
)
def get_sabatier_material_feed(
    material_id: int | None = Query(
        None, description="ид материала, с которого продолжается лента"
    ),
    show_next: bool = Query(
        False, alias="next", description="вернуть следующий материал за указанным ид"
    ),
    chemist_id: int | None = Depends(get_optional_chemist_id),
    session: Session = Depends(get_sabatier_session),
):
    if show_next and material_id is not None:
        material_id = get_next_material_id(session, material_id)
        if material_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    row = get_published_material(session, chemist_id, material_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_out(row, chemist_id)


@router.post(
    "",
    response_model=SabatierMaterialOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление материала",
    description=(
        "Создаёт черновик: кнопкой «Далее» заполняется только название. Создатель "
        "подставляется автоматически из сессии, с клиента его передать нельзя. "
        "Файлы необязательные: присланные уходят в MinIO под именами на латинице, "
        "в БД сохраняются только имена; без них остаются медиа по умолчанию "
        "с SSR-сервера. Метод создателя: гостю — 401."
    ),
    responses={
        201: {"description": "Черновик создан"},
        401: {"description": "Пользователь не аутентифицирован"},
        409: {"description": "У пользователя уже есть черновик"},
    },
)
def create_sabatier_material(
    material_name: str = Form(..., max_length=128, description="название материала"),
    material_image: UploadFile | None = File(None, description="изображение материала"),
    material_video: UploadFile | None = File(None, description="короткое видео материала"),
    chemist: ChemistUser = Depends(get_current_chemist),
    session: Session = Depends(get_sabatier_session),
):
    draft_exists = session.scalar(
        select(SabatierMaterial.id).where(
            SabatierMaterial.creator_chemist_id == chemist.id,
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
        creator_chemist_id=chemist.id,
        created_at=func.now(),
    )
    session.add(material)
    session.commit()
    return to_out(load_material_row(session, material.id, chemist.id), chemist.id)


@router.put(
    "/{material_id}/publish",
    response_model=SabatierMaterialOut,
    summary="Публикация материала",
    description=(
        "Заполняет краткое описание и оба поля по предметной области и переводит "
        "черновик в статус «опубликован». Статус с клиента не передаётся, дату "
        "формирования ставит бэкенд. Статусы меняются только вперёд: повторный вызов "
        "вернёт 404, вернуть материал в черновик нечем. Метод создателя: гостю — 401, "
        "на чужой материал — 403."
    ),
    responses={
        200: {"description": "Материал опубликован"},
        401: {"description": "Пользователь не аутентифицирован"},
        403: {"description": "Материал принадлежит другому пользователю"},
        404: {"description": "Материала нет или он уже не черновик"},
    },
)
def publish_sabatier_material(
    material_id: int,
    payload: SabatierMaterialPublishIn,
    chemist: ChemistUser = Depends(get_current_chemist),
    session: Session = Depends(get_sabatier_session),
):
    material = get_own_material(session, material_id, chemist.id)
    if material.material_status != MATERIAL_STATUS_DRAFT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    material.material_description = payload.material_description
    material.min_reaction_value = payload.min_reaction_value
    material.molar_mass = payload.molar_mass
    material.material_status = MATERIAL_STATUS_PUBLISHED
    material.formed_at = func.now()
    session.commit()
    return to_out(load_material_row(session, material_id, chemist.id), chemist.id)


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление материала",
    description=(
        "Только логическое удаление: статус меняется на «удалён», строка в БД остаётся. "
        "После него материал пропадает и из списка, и из ленты. Метод создателя: "
        "гостю — 401, на чужой материал — 403."
    ),
    responses={
        204: {"description": "Материал удалён логически"},
        401: {"description": "Пользователь не аутентифицирован"},
        403: {"description": "Материал принадлежит другому пользователю"},
        404: {"description": "Материала нет"},
    },
)
def delete_sabatier_material(
    material_id: int,
    chemist: ChemistUser = Depends(get_current_chemist),
    session: Session = Depends(get_sabatier_session),
):
    material = get_own_material(session, material_id, chemist.id)

    material.material_status = MATERIAL_STATUS_DELETED
    session.commit()


@router.post(
    "/{material_id}/like",
    response_model=SabatierMaterialOut,
    summary="Лайк материала",
    description=(
        "`liked` = 1 ставит лайк от пользователя из сессии, 0 — отменяет. Лайкать можно "
        "любой опубликованный материал, в том числе чужой, поэтому 403 здесь нет. "
        "В ответе видно новые `liked_count` и `is_liked`. Гостю — 401."
    ),
    responses={
        200: {"description": "Лайк изменён"},
        401: {"description": "Пользователь не аутентифицирован"},
        404: {"description": "Опубликованного материала с таким ид нет"},
    },
)
def like_sabatier_material(
    material_id: int,
    payload: MaterialLikeIn,
    chemist: ChemistUser = Depends(get_current_chemist),
    session: Session = Depends(get_sabatier_session),
):
    if get_published_material(session, chemist.id, material_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    like = session.scalar(
        select(MaterialLike).where(
            MaterialLike.chemist_id == chemist.id,
            MaterialLike.material_id == material_id,
        )
    )
    if payload.liked == 1 and like is None:
        session.add(MaterialLike(chemist_id=chemist.id, material_id=material_id))
    elif payload.liked == 0 and like is not None:
        session.delete(like)
    session.commit()

    return to_out(load_material_row(session, material_id, chemist.id), chemist.id)
