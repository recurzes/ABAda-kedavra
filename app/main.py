from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.params import Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, SessionLocal, engine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("address_book")

# DB setup
Base.metadata.create_all(bind=engine)


# App
app = FastAPI(
    title="Address Book API",
    description="Create, update, delete, and geographically search addresses"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post(
    "/addresses",
    response_model=schemas.AddressResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["addresses"]
)
def create_address(address: schemas.AddressCreate, db: Session = Depends(get_db)):
    return crud.create_address(db, address)


@app.get(
    "/addresses",
    response_model=List[schemas.AddressResponse],
    tags=["addresses"]
)
def list_addresses(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db)
):
    return crud.list_addresses(db, skip=skip, limit=limit)


@app.get(
    "/addresses/nearby",
    response_model=List[schemas.NearbyAddressResponse],
    tags=["addresses"]
)
def get_addresses_nearby(
        latitude: float = Query(..., ge=-90, le=90, description="Search center latitude"),
        longitude: float = Query(..., ge=-180, le=180, description="Search center longitude"),
        radius_km: float = Query(..., gt=0, le=20000, description="Search radius in kilometers"),
        db: Session = Depends(get_db)
):
    results = crud.find_addresses_near(db, latitude, longitude, radius_km)
    return [
        schemas.NearbyAddressResponse(
            **schemas.AddressResponse.model_validate(address).model_dump(),
            distance_km=round(distance, 3)
        )
        for address, distance in results
    ]


@app.get("/addresses/{address_id}", response_model=schemas.AddressResponse, tags=["addresses"])
def get_address(address_id: int, db: Session = Depends(get_db)):
    db_address = crud.get_address(db, address_id)
    if db_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return db_address


@app.put("/addresses/{address_id}", response_model=schemas.AddressResponse, tags=["addresses"])
def get_address(address_id: int, address: schemas.AddressUpdate, db: Session = Depends(get_db)):
    db_address = crud.update_address(db, address_id, address)
    if db_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return db_address


@app.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["addresses"])
def get_address(address_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_address(db, address_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return None
