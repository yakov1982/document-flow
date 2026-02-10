"""Сервис лицензирования и активации продукта."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy.orm import Session

from lexima_dms.db.models import License


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LicenseStatus(NamedTuple):
    active: bool
    expires_at: datetime | None
    message: str


def format_license_key(raw: str) -> str:
    """Форматирует ключ: убирает пробелы и дефисы, приводит к верхнему регистру."""
    return raw.replace(" ", "").replace("-", "").upper()


def generate_license_key() -> str:
    """Генерирует ключ формата XXXX-XXXX-XXXX-XXXX-XXXX (20 hex символов)."""
    raw = secrets.token_hex(10)  # 20 hex chars
    parts = [raw[i : i + 4] for i in range(0, 20, 4)]
    return "-".join(parts).upper()


def _ensure_aware(dt: datetime) -> datetime:
    """Приводит datetime к timezone-aware (UTC) если naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_active_license(db: Session) -> License | None:
    """Возвращает активную лицензию (активированную и не истёкшую)."""
    now = utcnow()
    return (
        db.query(License)
        .filter(License.activated_at.isnot(None), License.expires_at > now)
        .order_by(License.expires_at.desc())
        .first()
    )


def get_license_status(db: Session) -> LicenseStatus:
    """Возвращает текущий статус лицензии."""
    license_ = get_active_license(db)
    if license_:
        return LicenseStatus(
            active=True,
            expires_at=license_.expires_at,
            message=f"Лицензия активна до {license_.expires_at.strftime('%Y-%m-%d')}",
        )
    # Проверяем, есть ли неактивированная или истёкшая лицензия
    any_license = db.query(License).order_by(License.created_at.desc()).first()
    if any_license:
        if not any_license.activated_at:
            return LicenseStatus(
                active=False,
                expires_at=any_license.expires_at,
                message="Лицензия не активирована. Введите ключ для активации.",
            )
        if _ensure_aware(any_license.expires_at) <= utcnow():
            return LicenseStatus(
                active=False,
                expires_at=any_license.expires_at,
                message=f"Срок действия лицензии истёк {any_license.expires_at.strftime('%Y-%m-%d')}",
            )
    return LicenseStatus(
        active=False,
        expires_at=None,
        message="Продукт не активирован. Введите лицензионный ключ.",
    )


def activate_license(db: Session, license_key: str) -> LicenseStatus:
    """
    Активирует лицензию по ключу.
    Возвращает LicenseStatus. При успехе active=True.
    """
    key = format_license_key(license_key)
    license_ = db.query(License).filter(License.license_key == key).one_or_none()
    if not license_:
        return LicenseStatus(
            active=False,
            expires_at=None,
            message="Неверный лицензионный ключ",
        )
    if license_.activated_at:
        if _ensure_aware(license_.expires_at) > utcnow():
            return LicenseStatus(
                active=True,
                expires_at=license_.expires_at,
                message=f"Лицензия уже активирована, действует до {license_.expires_at.strftime('%Y-%m-%d')}",
            )
        return LicenseStatus(
            active=False,
            expires_at=license_.expires_at,
            message=f"Срок действия лицензии истёк {license_.expires_at.strftime('%Y-%m-%d')}",
        )
    if _ensure_aware(license_.expires_at) <= utcnow():
        return LicenseStatus(
            active=False,
            expires_at=license_.expires_at,
            message=f"Срок действия ключа истёк {license_.expires_at.strftime('%Y-%m-%d')}",
        )
    license_.activated_at = utcnow()
    db.commit()
    return LicenseStatus(
        active=True,
        expires_at=license_.expires_at,
        message=f"Лицензия успешно активирована до {license_.expires_at.strftime('%Y-%m-%d')}",
    )


def create_license(db: Session, expires_days: int = 365) -> License:
    """Создаёт новую лицензию (ключ генерируется). Используется в CLI."""
    key = generate_license_key()
    expires_at = utcnow() + timedelta(days=expires_days)
    # Храним нормализованный ключ для поиска при активации
    license_ = License(license_key=format_license_key(key), expires_at=expires_at)
    db.add(license_)
    db.commit()
    db.refresh(license_)
    # Возвращаем модель с форматированным ключом для отображения
    license_.license_key = key
    return license_
