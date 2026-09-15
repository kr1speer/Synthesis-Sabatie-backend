from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from data.sabatier_collections import sabatier_materials_db

router = APIRouter(prefix="/sabatier_materials")
templates = Jinja2Templates(directory="templates")


def get_published_sabatier_materials():
    return [m for m in sabatier_materials_db if m["status"] == "published"]



@router.get("/feed")
@router.get("/feed/{material_id}")
def get_sabatier_material_feed(
    request: Request,
    material_id: int = None,
    show_next: bool = Query(False, alias="next"),
):
    published = get_published_sabatier_materials()

    if not published:
        return templates.TemplateResponse(
            request=request,
            name="sabatier_feed.html",
            context={"material": None, "liked_count": 0},
        )

    if material_id is None:
        material_id = published[0]["id"]

    if show_next:
        published_ids = [m["id"] for m in published]
        if material_id in published_ids:
            idx = published_ids.index(material_id)
            next_material = published[(idx + 1) % len(published)]
        else:
            next_material = published[0]
        return RedirectResponse(url=f"/sabatier_materials/feed/{next_material['id']}")

    material = next((m for m in published if m["id"] == material_id), published[0])
    liked_count = len(material["liked_user_ids"])

    return templates.TemplateResponse(
        request=request,
        name="sabatier_feed.html",
        context={"material": material, "liked_count": liked_count},
    )



@router.get("/draft")
def get_sabatier_material_draft(request: Request):
    draft = next(
        (m for m in sabatier_materials_db if m["status"] == "draft"), None
    )
    return templates.TemplateResponse(
        request=request,
        name="sabatier_draft.html",
        context={"draft": draft},
    )



@router.get("")
def get_sabatier_materials_catalog(request: Request, min_reaction_value: str = None):
    published = get_published_sabatier_materials()

    parsed_min_reaction_value = 0
    if min_reaction_value and min_reaction_value.strip().isdigit():
        parsed_min_reaction_value = int(min_reaction_value)

    materials = [
        {**m, "liked_count": len(m["liked_user_ids"])}
        for m in published
        if m["min_reaction_value"] >= parsed_min_reaction_value
    ]

    slider_max = max((m["min_reaction_value"] for m in published), default=0)

    return templates.TemplateResponse(
        request=request,
        name="sabatier_catalog.html",
        context={
            "materials": materials,
            "min_reaction_value": parsed_min_reaction_value,
            "slider_max": slider_max,
        },
    )
