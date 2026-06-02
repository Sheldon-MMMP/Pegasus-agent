from fastapi import APIRouter

from agent_server.schemas import SettingsDTO, UpdateSettingsRequest
from agent_server.services.settings import get_settings as get_settings_service
from agent_server.services.settings import update_settings as update_settings_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsDTO)
def get_settings() -> SettingsDTO:
    return get_settings_service()


@router.put("", response_model=SettingsDTO)
def update_settings(request: UpdateSettingsRequest) -> SettingsDTO:
    return update_settings_service(request)
