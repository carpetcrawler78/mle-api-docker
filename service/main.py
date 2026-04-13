from fastapi import Depends, FastAPI, HTTPException
import models
import schemas
from database import engine, SessionLocal
from sqlalchemy.orm import Session


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
def index():
    return {"data": "user list"}


# Get all users
@app.get("/users", response_model=list[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# Add user
@app.post("/users", response_model=schemas.UserOut)
def create_user(request: schemas.UserModel, db: Session = Depends(get_db)):
    new_user = models.User(
        name=request.name, email=request.email, password=request.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Update user
@app.put("/users/{id}")
def update_user(id: int, request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id)
    existing_user = user.first()
    if existing_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in request.model_dump().items():
        setattr(existing_user, field, value)

    db.commit()
    return "Updated successfully"


# Delete user
@app.delete("/users/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id)
    if not user.first():
        raise HTTPException(status_code=404, detail="User not found")
    user.delete(synchronize_session=False)
    db.commit()
    return "Deleted successfully"
