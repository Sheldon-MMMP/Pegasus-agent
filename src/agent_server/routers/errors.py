from fastapi import HTTPException

from agent_server.schemas import ErrorDTO
from agent_server.services.exceptions import ServiceError


DEFAULT_SERVICE_ERROR_STATUS_CODES = {
    "invalid_skill_name": 422,
    "skill_already_exists": 409,
    "skill_file_already_exists": 409,
    "skill_file_write_failed": 500,
}


def raise_http_error_from_service_error(
    error: ServiceError,
    status_codes: dict[str, int] | None = None,
) -> None:
    merged_status_codes = {
        **DEFAULT_SERVICE_ERROR_STATUS_CODES,
        **(status_codes or {}),
    }

    error_dto = ErrorDTO(
        code=error.code,
        message=error.message,
        details=error.details,
    )

    raise HTTPException(
        status_code=merged_status_codes.get(error.code, 500),
        detail=error_dto.model_dump(),
    )