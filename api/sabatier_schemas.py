from pydantic import BaseModel, ConfigDict, Field


class SabatierMaterialOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    material_name: str
    material_description: str | None
    material_image_name: str
    material_video_name: str
    min_reaction_value: int | None
    molar_mass: float | None
    liked_count: int
    is_mine: int = 0
    is_liked: int = 0


class SabatierMaterialPublishIn(BaseModel):

    material_description: str = Field(max_length=1024)
    min_reaction_value: int = Field(ge=0)
    molar_mass: float = Field(gt=0)


class MaterialLikeIn(BaseModel):

    liked: int = Field(ge=0, le=1)


class ChemistUserRegisterIn(BaseModel):

    chemist_login: str = Field(min_length=1, max_length=64)
    chemist_password: str = Field(min_length=1, max_length=128)
    full_name: str = Field(min_length=1, max_length=128)


class ChemistUserLoginIn(BaseModel):

    chemist_login: str = Field(min_length=1, max_length=64)
    chemist_password: str = Field(min_length=1, max_length=128)


class ChemistUserOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    chemist_login: str
    full_name: str
