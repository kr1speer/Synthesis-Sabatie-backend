from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
    select,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column

from data.sabatier_database import Base

MATERIAL_STATUS_DRAFT = "draft"
MATERIAL_STATUS_PUBLISHED = "published"
MATERIAL_STATUS_DELETED = "deleted"

DEFAULT_MATERIAL_IMAGE_NAME = "default_material.png"
DEFAULT_MATERIAL_VIDEO_NAME = "default_material.mp4"


class ChemistUser(Base):

    __tablename__ = "chemist_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chemist_login: Mapped[str] = mapped_column(String(64))
    chemist_password: Mapped[str] = mapped_column(String(128))
    full_name: Mapped[str] = mapped_column(String(128))
    is_moderator: Mapped[bool] = mapped_column(Boolean)


class MaterialLike(Base):

    __tablename__ = "material_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chemist_id: Mapped[int] = mapped_column(ForeignKey("chemist_users.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("sabatier_materials.id"))


class SabatierMaterial(Base):

    __tablename__ = "sabatier_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_name: Mapped[str] = mapped_column(String(128))
    material_description: Mapped[str | None] = mapped_column(String(1024))
    material_status: Mapped[str] = mapped_column(String(16))
    material_image_name: Mapped[str] = mapped_column(String(128))
    material_video_name: Mapped[str] = mapped_column(String(128))
    min_reaction_value: Mapped[int | None] = mapped_column(Integer)
    molar_mass: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    creator_chemist_id: Mapped[int] = mapped_column(ForeignKey("chemist_users.id"))
    formed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


SabatierMaterial.liked_count = column_property(
    select(func.count(MaterialLike.id))
    .where(MaterialLike.material_id == SabatierMaterial.id)
    .scalar_subquery()
)
