"""API для активации лицензии и проверки статуса."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lexima_dms.api.deps import get_db
from lexima_dms.api.schemas import LicenseActivateIn, LicenseStatusOut
from lexima_dms.services.license import LicenseStatus, activate_license, get_license_status

router = APIRouter(prefix="/license", tags=["license"])


@router.get("/status", response_model=LicenseStatusOut)
def status(db: Session = Depends(get_db)) -> LicenseStatusOut:
    """Возвращает статус лицензии. Доступен без активации."""
    s: LicenseStatus = get_license_status(db)
    return LicenseStatusOut(active=s.active, expires_at=s.expires_at, message=s.message)


@router.post("/activate", response_model=LicenseStatusOut)
def activate(body: LicenseActivateIn, db: Session = Depends(get_db)) -> LicenseStatusOut:
    """Активирует продукт по лицензионному ключу. Доступен без активной лицензии."""
    s: LicenseStatus = activate_license(db, body.license_key)
    return LicenseStatusOut(active=s.active, expires_at=s.expires_at, message=s.message)
