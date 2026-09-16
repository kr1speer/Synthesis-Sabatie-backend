from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data.sabatier_database import engine, get_sabatier_session
from data.sabatier_models import (
    MATERIAL_STATUS_DRAFT,
    MATERIAL_STATUS_PUBLISHED,
    SabatierMaterial,
)

router = APIRouter(prefix="/sabatier_materials")
templates = Jinja2Templates(directory="templates")

templates.env.globals["default_material_image_url"] = "/static/img/default_material.png"
templates.env.globals["default_material_video_url"] = "/static/img/default_material.mp4"

CURRENT_CHEMIST_ID = 1


def get_published_materials(session: Session):
    query = (
        select(SabatierMaterial)
        .where(SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED)
        .order_by(SabatierMaterial.id)
    )
    return session.scalars(query).all()


def get_current_chemist_draft(session: Session):
    query = select(SabatierMaterial).where(
        SabatierMaterial.creator_chemist_id == CURRENT_CHEMIST_ID,
        SabatierMaterial.material_status == MATERIAL_STATUS_DRAFT,
    )
    return session.scalar(query)


def redirect_to(url: str):
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/feed")
@router.get("/feed/{material_id}")
def get_sabatier_material_feed(
    request: Request,
    material_id: int = None,
    show_next: bool = Query(False, alias="next"),
    session: Session = Depends(get_sabatier_session),
):
    materials = get_published_materials(session)
    material_ids = [m.id for m in materials]

    if material_id is None:
        material = materials[0] if materials else None
    elif material_id in material_ids:
        index = material_ids.index(material_id)
        if show_next:
            next_material = materials[(index + 1) % len(materials)]
            return redirect_to(f"/sabatier_materials/feed/{next_material.id}")
        material = materials[index]
    else:
        material = None

    return templates.TemplateResponse(
        request=request,
        name="sabatier_feed.html",
        context={"material": material},
        status_code=status.HTTP_200_OK if material else status.HTTP_404_NOT_FOUND,
    )



@router.get("/draft")
def get_sabatier_material_draft(
    request: Request,
    session: Session = Depends(get_sabatier_session),
):
    return templates.TemplateResponse(
        request=request,
        name="sabatier_draft.html",
        context={"draft": get_current_chemist_draft(session)},
    )


@router.post("/draft")
def create_sabatier_material_draft(
    material_name: str = Form(..., max_length=128),
    reaction_role: str = Form(..., max_length=1024),
    session: Session = Depends(get_sabatier_session),
):
    if get_current_chemist_draft(session) is None:
        session.add(
            SabatierMaterial(
                material_name=material_name,
                reaction_role=reaction_role,
                material_status=MATERIAL_STATUS_DRAFT,
                creator_chemist_id=CURRENT_CHEMIST_ID,
                created_at=func.now(),
            )
        )
        session.commit()
    return redirect_to("/sabatier_materials/draft")



@router.post("/draft/publish")
def publish_sabatier_material_draft(
    material_name: str = Form(..., max_length=128),
    reaction_role: str = Form(..., max_length=1024),
    min_reaction_value: int = Form(..., ge=0),
    molar_mass: Decimal = Form(..., gt=0),
    session: Session = Depends(get_sabatier_session),
):
    draft = get_current_chemist_draft(session)
    if draft is None:
        return redirect_to("/sabatier_materials/draft")

    draft.material_name = material_name
    draft.reaction_role = reaction_role
    draft.min_reaction_value = min_reaction_value
    draft.molar_mass = molar_mass
    draft.material_status = MATERIAL_STATUS_PUBLISHED
    draft.formed_at = func.now()
    session.commit()
    return redirect_to("/sabatier_materials")



@router.post("/{material_id}/delete")
def delete_sabatier_material(material_id: int):
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE sabatier_materials SET material_status = 'deleted' WHERE id = %s",
            (material_id,),
        )
        connection.commit()
        cursor.close()
    finally:
        connection.close()
    return redirect_to("/sabatier_materials")



@router.get("")
def get_sabatier_materials_catalog(
    request: Request,
    min_reaction_value: int = 0,
    session: Session = Depends(get_sabatier_session),
):
    query = (
        select(SabatierMaterial)
        .where(SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED)
        .order_by(SabatierMaterial.id)
    )
    if min_reaction_value > 0:
        query = query.where(SabatierMaterial.min_reaction_value >= min_reaction_value)
    materials = session.scalars(query).all()

    slider_max = session.scalar(
        select(func.max(SabatierMaterial.min_reaction_value)).where(
            SabatierMaterial.material_status == MATERIAL_STATUS_PUBLISHED
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="sabatier_catalog.html",
        context={
            "materials": materials,
            "min_reaction_value": min_reaction_value,
            "slider_max": slider_max or 0,
        },
    )
