import logging

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import FileResponse
from urllib.parse import unquote

from .db import SessionLocal, SessionLocalSQLServer   # Đảm bảo có file db.py định nghĩa SessionLocal
from .models import User, Vehicle, PhieuNhap  # Đảm bảo có file models.py định nghĩa User và Vehicle
from enum import Enum

from fastapi import Query

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Khởi tạo VideoProcessor

cam_truoc_running = False
cam_sau_running = False


# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
camera_url_truoc = 'rtsp://admin:Quangtri2024@192.168.1.123'
camera_url_sau = 'rtsp://admin:Quangtri2024@192.168.1.122'

@app.on_event("startup")
def startup_event():
    logging.debug("Starting up the app...")

@app.get("/")
def read_root():
    return {"message": "Welcome to the vehicle counting API"}

        
# Định nghĩa các mô hình người dùng
class UserCreate(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: str = None
    password: str = None

class UserResponse(BaseModel):
    id: int
    username: str
    password: str

class CarType(str, Enum):
    xe_con = "xe_con"
    xe_tai = "xe_tai"
    xe_cau = "xe_cau"
    xe_cong_nong = "xe_cong_nong"
    xe_nang = "xe_nang"

# Định nghĩa các mô hình phương tiện
class VehicleCreate(BaseModel):
    trackIdCamTruoc: Optional[str] = None  # Cập nhật theo mô hình mới
    trackIdCamSau: Optional[str] = None  # Cập nhật theo mô hình mới
    direction: str
    image_path_cam_truoc: Optional[str] = None
    image_path_cam_sau: Optional[str] = None
    car_type: Optional[CarType] = None  # Sử dụng enum CarType
    createdAt: Optional[datetime] = None  # Thêm trường createdAt
    updatedAtByCamTruoc: Optional[datetime] = None  # Thêm trường updatedAtByCamTruoc
    updatedAtByCamSau: Optional[datetime] = None  # Thêm trường updatedAtByCamSau

class VehicleResponse(BaseModel):
    id: int
    createdAt: datetime
    updatedAtByCamTruoc: Optional[datetime] = None
    updatedAtByCamSau: Optional[datetime] = None
    trackIdCamTruoc: Optional[str] = None  # Cập nhật theo mô hình mới
    trackIdCamSau: Optional[str] = None  # Cập nhật theo mô hình mới
    direction: Optional[str] = None
    image_path_cam_truoc: Optional[str] = None
    image_path_cam_sau: Optional[str] = None
    car_type: Optional[CarType] = None  # Sử dụng enum CarType
    class Config:
        from_attributes = True  # Thêm dòng này để hỗ trợ from_orm

# Dependency để lấy phiên làm việc với cơ sở dữ liệu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint cho người dùng
@app.post("/register/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    db_user = User(username=user.username, password=user.password)  # Lưu mật khẩu trực tiếp
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserResponse])
def get_all_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.put("/forgot-password/{username}", response_model=UserResponse)
def update_user(username: str, user: UserUpdate, db: Session = Depends(get_db)):
    # Kiểm tra xem username có tồn tại không
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Cập nhật thông tin người dùng
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# API lấy thông tin người dùng theo ID
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    print("db_user:", db_user.__dict__)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# API đăng nhập
@app.post("/login/")
def login(username: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user and db_user.password == password:  # So sánh mật khẩu trực tiếp
        return {"success": True}
    return {"success": False}

@app.post("/vehicles/", response_model=dict)
def get_vehicles(
    params: dict,  # Tham số truyền vào dưới dạng dictionary
    db: Session = Depends(get_db)
):
    skip = params.get('skip', 0)
    limit = params.get('limit', 10)
    start_date = params.get('start_date', None)
    end_date = params.get('end_date', None)
    direction = params.get('direction', None)
    car_type = params.get('car_type', None)
    
    # In để kiểm tra giá trị các tham số
    print("start_date1", start_date)
    print("end_date1", end_date)
    
    query = db.query(Vehicle)

    # Giữ nguyên start_date và end_date nếu chúng được truyền vào
    if start_date and end_date:
        query = query.filter(Vehicle.createdAt.between(start_date, end_date))
    elif start_date:
        query = query.filter(Vehicle.createdAt >= start_date)
    elif end_date:
        query = query.filter(Vehicle.createdAt <= end_date)

    print("start_date2", start_date)
    print("end_date2", end_date)

    # Áp dụng bộ lọc thời gian
    if direction:
        query = query.filter(Vehicle.direction == direction)

    if car_type:
        car_type = unquote(car_type)  # Giải mã chuỗi car_type
        car_type_list = car_type.split(",")  # Tách chuỗi car_type thành danh sách
        query = query.filter(Vehicle.car_type.in_(car_type_list))

    print("car_type", car_type)

    # Lấy tổng số bản ghi trước khi phân trang
    total_records = query.count()

    # Phân trang
    vehicles = query.offset(skip).limit(limit).all()

    # Chuyển đổi danh sách Vehicle thành VehicleResponse
    vehicle_responses = [VehicleResponse.from_orm(vehicle) for vehicle in vehicles]

    return {
        "total_records": total_records,
        "vehicles": vehicle_responses
    }

@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@app.get("/getImage/")
def get_image(image_path: str):
    # Kiểm tra nếu tệp có tồn tại
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Trả về hình ảnh
    return FileResponse(image_path)

def get_sql_db():
    sql_server_db = SessionLocalSQLServer()
    try:
        yield sql_server_db
    finally:
        sql_server_db.close()

def check_and_save_vehicle_cam_truoc(vehicle, db: Session, current_time: datetime):
    # Lấy 10 phương tiện gần đây nhất
    vehicles = db.query(Vehicle).order_by(Vehicle.createdAt.desc()).limit(10).all()

    # Kiểm tra nếu không có phương tiện nào
    if not vehicles:
        print("No vehicles found, creating new vehicle.")
        new_vehicle = Vehicle(
            trackIdCamTruoc=vehicle.trackIdCamTruoc,
            direction=vehicle.direction,
            image_path_cam_truoc=vehicle.image_path_cam_truoc,
            car_type=vehicle.car_type,
            createdAt=current_time,
            updatedAtByCamTruoc=current_time
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        return {"message": "Not vehicles so Created new vehicle", "trackIdCamTruoc": vehicle.trackIdCamTruoc}
    
    # Kiểm tra thời gian chênh lệch và các điều kiện khác
    if all((current_time - vehicle.createdAt).total_seconds() > 300 for vehicle in vehicles):
        new_vehicle = Vehicle(
            trackIdCamTruoc=vehicle.trackIdCamTruoc,
            direction=vehicle.direction,
            image_path_cam_truoc=vehicle.image_path_cam_truoc,
            car_type=vehicle.car_type,
            createdAt=current_time,
            updatedAtByCamTruoc=current_time
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        return {"message": "Created new vehicle", "trackIdCamTruoc": vehicle.trackIdCamTruoc}
    
    # Kiểm tra các phương tiện có cùng direction và trackIdCamTruoc trong vòng 3 phút
    for db_vehicle in vehicles:
        time_diff = (current_time - db_vehicle.createdAt).total_seconds()

        # Cập nhật phương tiện nếu thỏa mãn điều kiện
        if time_diff < 180 and db_vehicle.direction == vehicle.direction and db_vehicle.trackIdCamTruoc == vehicle.trackIdCamTruoc:
            if db_vehicle.updatedAtByCamTruoc is None:
                db_vehicle.updatedAtByCamTruoc = current_time
            if db_vehicle.image_path_cam_truoc is None:
                db_vehicle.image_path_cam_truoc = vehicle.image_path_cam_truoc
            db.commit()
            return {"message": "Updated existing vehicle based on time difference", "trackIdCamTruoc": vehicle.trackIdCamTruoc}

        # Kiểm tra nếu có sự trùng lặp với direction nhưng trackIdCamTruoc là None
        if time_diff < 180 and db_vehicle.direction == vehicle.direction and db_vehicle.trackIdCamTruoc is None:
            if db_vehicle.updatedAtByCamTruoc is None:
                db_vehicle.updatedAtByCamTruoc = current_time
            if db_vehicle.image_path_cam_truoc is None:
                db_vehicle.image_path_cam_truoc = vehicle.image_path_cam_truoc
            db_vehicle.trackIdCamTruoc = vehicle.trackIdCamTruoc
            db.commit()
            return {"message": "Updated existing vehicle with new trackIdCamTruoc", "trackIdCamTruoc": vehicle.trackIdCamTruoc}
    
    # Nếu không thỏa mãn điều kiện nào, tạo mới phương tiện
    new_vehicle = Vehicle(
        trackIdCamTruoc=vehicle.trackIdCamTruoc,
        direction=vehicle.direction,
        image_path_cam_truoc=vehicle.image_path_cam_truoc,
        car_type=vehicle.car_type,
        createdAt=current_time,
        updatedAtByCamTruoc=current_time
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return {"message": "Created new vehicle", "trackIdCamTruoc": vehicle.trackIdCamTruoc}

def check_and_save_vehicle_cam_sau(vehicle, db: Session, current_time: datetime):
    # Lấy 10 phương tiện gần đây nhất
    vehicles = db.query(Vehicle).order_by(Vehicle.createdAt.desc()).limit(10).all()
    print("call2")

    # Kiểm tra nếu không có phương tiện nào
    if not vehicles:
        print("No vehicles found, creating new vehicle.")
        new_vehicle = Vehicle(
            trackIdCamSau=vehicle.trackIdCamSau,
            direction=vehicle.direction,
            image_path_cam_sau=vehicle.image_path_cam_sau,
            car_type=vehicle.car_type,
            createdAt=current_time,
            updatedAtByCamSau=current_time
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        return {"message": "Not vehicles so Created new vehicle", "trackIdCamSau": vehicle.trackIdCamSau}
    
    # Kiểm tra thời gian chênh lệch và các điều kiện khác
    if all((current_time - vehicle.createdAt).total_seconds() > 300 for vehicle in vehicles):
        print("call2.2.2.2")
        new_vehicle = Vehicle(
            trackIdCamSau=vehicle.trackIdCamSau,
            direction=vehicle.direction,
            image_path_cam_sau=vehicle.image_path_cam_sau,
            car_type=vehicle.car_type,
            createdAt=current_time,
            updatedAtByCamSau=current_time
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        return {"message": "Created new vehicle", "trackIdCamSau": vehicle.trackIdCamSau}
    
    # Kiểm tra các phương tiện có cùng direction và trackIdCamSau trong vòng 3 phút
    for db_vehicle in vehicles:
        time_diff = (current_time - db_vehicle.createdAt).total_seconds()

        # Cập nhật phương tiện nếu thỏa mãn điều kiện
        if time_diff < 180 and db_vehicle.direction == vehicle.direction and db_vehicle.trackIdCamSau == vehicle.trackIdCamSau:
            if db_vehicle.updatedAtByCamSau is None:
                db_vehicle.updatedAtByCamSau = current_time
            if db_vehicle.image_path_cam_sau is None:
                db_vehicle.image_path_cam_sau = vehicle.image_path_cam_sau
            db.commit()
            return {"message": "Updated existing vehicle based on time difference", "trackIdCamSau": vehicle.trackIdCamSau}

        # Kiểm tra nếu có sự trùng lặp với direction nhưng trackIdCamSau là None
        if time_diff < 180 and db_vehicle.direction == vehicle.direction and db_vehicle.trackIdCamSau is None:
            if db_vehicle.updatedAtByCamSau is None:
                db_vehicle.updatedAtByCamSau = current_time
            if db_vehicle.image_path_cam_sau is None:
                db_vehicle.image_path_cam_sau = vehicle.image_path_cam_sau
            db_vehicle.trackIdCamSau = vehicle.trackIdCamSau
            db.commit()
            return {"message": "Updated existing vehicle with new trackIdCamSau", "trackIdCamSau": vehicle.trackIdCamSau}
    
    # Nếu không thỏa mãn điều kiện nào, tạo mới phương tiện
    new_vehicle = Vehicle(
        trackIdCamSau=vehicle.trackIdCamSau,
        direction=vehicle.direction,
        image_path_cam_sau=vehicle.image_path_cam_sau,
        car_type=vehicle.car_type,
        createdAt=current_time,
        updatedAtByCamSau=current_time
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return {"message": "Created new vehicle", "trackIdCamSau": vehicle.trackIdCamSau}

@app.post("/create-vehicles/")
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    current_time = vehicle.createdAt or datetime.utcnow()
    print("vehicleDTO=", vehicle)
    # Gọi hàm kiểm tra và lưu phương tiện
    if vehicle.trackIdCamTruoc:
        result = check_and_save_vehicle_cam_truoc(vehicle, db, current_time)
    
    # Kiểm tra nếu trackIdCamSau tồn tại, gọi check_and_save_vehicle_cam_sau
    if vehicle.trackIdCamSau:
        print("call1")
        result = check_and_save_vehicle_cam_sau(vehicle, db, current_time)
    
    return result
        
@app.get("/phieu_nhap")
def get_phieu_nhap(
    page: int = Query(1, ge=1),  # Số trang, bắt đầu từ 1
    size: int = Query(10, ge=1),  # Kích thước mỗi trang
    sophieu: Optional[str] = None,  # Bộ lọc theo số phiếu
    bienso: Optional[str] = None,  # Bộ lọc theo biển số
    loaihinh: Optional[str] = None,  # Bộ lọc theo loại hình
    sql_server_db: Session = Depends(get_sql_db)
):
    print("call1")
    query = sql_server_db.query(PhieuNhap)
    print("call2", query.statement)

    # Áp dụng bộ lọc
    if sophieu:
        query = query.filter(PhieuNhap.sophieu.like(f"%{sophieu}%"))
    if bienso:
        query = query.filter(PhieuNhap.bienso.like(f"%{bienso}%"))
    if loaihinh:
        query = query.filter(PhieuNhap.loaihinh.like(f"%{loaihinh}%"))

    print("call3", query.statement)

    query = query.order_by(PhieuNhap.ngaytao.desc())
    # Tính toán phân trang
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.112", port=8000, log_level="info", reload=True)
