from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.sabatier_database import Base

MATERIAL_STATUS_DRAFT = "draft"
MATERIAL_STATUS_PUBLISHED = "published"
MATERIAL_STATUS_DELETED = "deleted"


class ChemistUser(Base):

    __tablename__ = "chemist_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chemist_login: Mapped[str] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(128))
    is_moderator: Mapped[bool] = mapped_column(Boolean)


class SabatierMaterial(Base):

    __tablename__ = "sabatier_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_name: Mapped[str] = mapped_column(String(128))
    reaction_role: Mapped[str] = mapped_column(String(1024))
    material_status: Mapped[str] = mapped_column(String(16))
    material_image_url: Mapped[str | None] = mapped_column(String(512))
    material_video_url: Mapped[str | None] = mapped_column(String(512))
    # server_default: у черновика поля по теме ещё не заданы, СУБД подставит 0
    min_reaction_value: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    molar_mass: Mapped[Decimal] = mapped_column(Numeric(8, 3), server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    creator_chemist_id: Mapped[int] = mapped_column(ForeignKey("chemist_users.id"))
    formed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    likes: Mapped[list["MaterialLike"]] = relationship()


class MaterialLike(Base):

    __tablename__ = "material_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chemist_id: Mapped[int] = mapped_column(ForeignKey("chemist_users.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("sabatier_materials.id"))
