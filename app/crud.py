import logging
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app import models, schemas
from app.geo_utils import bounding_box, haversine_distance_km

logger = logging.getLogger("address_book")


def create_address(db: Session, address: schemas.AddressCreate) -> models.Address:
    db_address = models.Address(**address.model_dump())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    logger.info("Created address id=%s (%s, %s)", db_address.id, db_address.city, db_address.country)
    return db_address


def get_address(db: Session, address_id: int) -> Optional[models.Address]:
    return db.query(models.Address).filter(models.Address.id == address_id).first()


def list_addresses(db: Session, skip: int = 0, limit: int = 100) -> List[models.Address]:
    return db.query(models.Address).offset(skip).limit(limit).all()


def update_address(
        db: Session,
        address_id: int,
        address_update: schemas.AddressUpdate
) -> Optional[models.Address]:
    db_address = get_address(db, address_id)
    if db_address is None:
        return None

    update_data = address_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_address, field, value)

    db.commit()
    db.refresh(db_address)
    logger.info("Updated address id=%s (fields: %s)", address_id, list(update_data.keys()))
    return db_address


def delete_address(db: Session, address_id: int) -> bool:
    db_address = get_address(db, address_id)
    if db_address is None:
        return False

    db.delete(db_address)
    db.commit()
    logger.info("Deleted address id=%s", address_id)
    return True


def find_addresses_near(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float
) -> List[tuple[models.Address, float]]:
    """
    Return (address, distance_km) pairs for every address within
    `radius_km` of (latitude, longitude), sorted nearest-first.

    Two-step search:
        1. A cheap SQL bounding-box filter using the indexed lat/lon columns,
             to avoid scanning the whole table.
        2. An exact haversine distance check + sort in Python on that
            (much smaller) candidate set, since SQLite has no built-in
            great-circle distance function.
    """
    lat_min, lat_max, lon_min, lon_max = bounding_box(latitude, longitude, radius_km)

    candidates = (
        db.query(models.Address)
        .filter(
            and_(
                models.Address.latitude >= lat_min,
                models.Address.latitude <= lat_max,
                models.Address.longitude >= lon_min,
                models.Address.longitude <= lon_max
            )
        )
        .all()
    )

    results = []
    for candidate in candidates:
        distance = haversine_distance_km(latitude, longitude, candidate.latitude, candidate.longitude)
        if distance <= radius_km:
            results.append((candidate, distance))

    results.sort(key=lambda pair: pair[1])
    logger.info(
        "Nearby search at (%.5f, %.5f) radius=%.2fkm -> %d result(s)",
        latitude,
        longitude,
        radius_km,
        len(results)
    )
    return results