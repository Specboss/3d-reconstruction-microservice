import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class ResourcesConfigModel(BaseModel):
    max_concurrent_jobs: int = Field(default=1, ge=1)
    gpu_required: bool = False
    timeout_seconds: int = Field(default=7200, ge=0)

    model_config = ConfigDict(extra="ignore")


class FeatureExtractionConfigModel(BaseModel):
    describer_types: list[str] = Field(alias="describerTypes")
    describer_preset: str = Field(alias="describerPreset")
    force_cpu_extraction: bool = Field(alias="forceCpuExtraction", default=False)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class DepthMapConfigModel(BaseModel):
    downscale: int = 1
    use_gpu: bool = Field(alias="useGpu", default=True)
    min_view_angle: int = Field(alias="minViewAngle")
    max_view_angle: int = Field(alias="maxViewAngle")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class MeshingConfigModel(BaseModel):
    max_points: int = Field(alias="maxPoints")
    max_input_points: int = Field(alias="maxInputPoints")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class TexturingConfigModel(BaseModel):
    texture_side: int = Field(alias="textureSide")
    unwrap_method: str = Field(alias="unwrapMethod")
    padding: int

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class DefaultsConfigModel(BaseModel):
    feature_extraction: FeatureExtractionConfigModel
    depthmap: DepthMapConfigModel
    meshing: MeshingConfigModel
    texturing: TexturingConfigModel

    model_config = ConfigDict(extra="ignore")


class MeshroomConfigModel(BaseModel):
    binary: str
    pipeline_path: str
    workspace_dir: str = "/var/lib/meshroom"
    resources: ResourcesConfigModel
    defaults: DefaultsConfigModel

    model_config = ConfigDict(extra="ignore")


class LoggingConfigModel(BaseModel):
    level: str = "INFO"

    model_config = ConfigDict(extra="ignore")


class AwsConfigModel(BaseModel):
    endpoint_url: str
    default_region: str
    use_ssl: bool = False
    bucket_name: str

    model_config = ConfigDict(extra="ignore")


class JsonConfigModel(BaseModel):
    logging: LoggingConfigModel
    aws: AwsConfigModel
    meshroom: MeshroomConfigModel

    model_config = ConfigDict(extra="ignore")


class SecretSettings(BaseSettings):
    aws_access_key_id: str = Field(alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class AppSettings(BaseModel):
    logging: LoggingConfigModel
    aws: AwsConfigModel
    meshroom: MeshroomConfigModel
    secrets: SecretSettings

    model_config = ConfigDict(extra="ignore")


def _resolve_config_path() -> Path:
    return Path(__file__).resolve().parent.parent.joinpath("config", "app_config.json")


def _load_config_data(path: Path) -> JsonConfigModel:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open(encoding="utf-8") as config_file:
        raw_data: dict[str, Any] = json.load(config_file)

    return JsonConfigModel.model_validate(raw_data)


def _build_settings(
    config_model: JsonConfigModel,
    secrets: SecretSettings,
) -> AppSettings:
    return AppSettings(
        logging=config_model.logging,
        aws=config_model.aws,
        meshroom=config_model.meshroom,
        secrets=secrets,
    )


@lru_cache
def get_settings() -> AppSettings:
    config_path = _resolve_config_path()
    json_config = _load_config_data(config_path)
    secret_settings = SecretSettings()
    return _build_settings(json_config, secret_settings)
