import logging

from fastapi import FastAPI, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import FileResponse
from urllib.parse import unquote
from sqlalchemy.sql import func

from .db import SessionLocal, SessionLocalSQLServer   # Đảm bảo có file db.py định nghĩa SessionLocal
from .models import User, Vehicle, PhieuNhap, UserNew, tblLoaiHinh, tblDmHang, tblDmKH  # Đảm bảo có file models.py định nghĩa User và Vehicle
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

class PhieuNhapUpdate(BaseModel):
    sophieu: Optional[str] = None
    ngay: Optional[datetime] = None
    bienso: Optional[str] = None
    taixe: Optional[str] = None
    loaihinh: Optional[str] = None
    canlan1: Optional[float] = None
    canlan2: Optional[float] = None
    giovao: Optional[datetime] = None
    giora: Optional[datetime] = None
    loaihang: Optional[str] = None
    hopdong: Optional[str] = None
    ghichu: Optional[str] = None
    dongia: Optional[float] = None
    is_thu_cong: Optional[bool] = None
    nguoicapnhat: Optional[str] = None  # Add nguoicapnhat for updates

    class Config:
        orm_mode = True  # Ensure ORM mapping is enabled
        from_attributes = True  # This allows from_orm to work correctly

class PhieuNhapResponse(BaseModel):
    id: int
    sophieu: str
    ngay: datetime
    bienso: str
    taixe: str
    loaihinh: str
    canlan1: Optional[float]
    canlan2: Optional[float]
    giovao: Optional[datetime]
    giora: Optional[datetime]
    loaihang: str
    hopdong: str
    ghichu: Optional[str]
    ngaytao: datetime
    nguoitao: str  # Creator
    ngaycapnhat: Optional[datetime]
    nguoicapnhat: Optional[str]  # Last updater
    logChinhSua: Optional[str]
    idThe: Optional[str]
    dongia: Optional[float]
    is_thu_cong: bool

    class Config:
        orm_mode = True  # To work with ORM models like SQLAlchemy

class PasswordUpdate(BaseModel):
    oldpassword: str
    newpassword: str
       
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

class PhieuNhapCreate(BaseModel):
    bienso: str
    taixe: Optional[str] = None
    loaihinh: str
    canlan1: Optional[float] = None
    canlan2: Optional[float] = None
    giovao: Optional[datetime] = None
    giora: Optional[datetime] = None
    loaihang: str
    hopdong: Optional[datetime] = ""
    ghichu: Optional[str] = None
    dongia: Optional[float] = None
    is_thu_cong: Optional[bool] = True
    nguoitao: str  # Add the user (creator) directly in the DTO

    class Config:
        orm_mode = True
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

class UserNewCreate(BaseModel):
    username: str
    password: str
    ho: Optional[str] = None
    ten: Optional[str] = None
    quyen: Optional[str] = None
    dienthoai: Optional[str] = None
    diachi: Optional[str] = None
    trangthai: Optional[bool] = None  # Đảm bảo đúng kiểu dữ liệu

class UserNewResponse(BaseModel):
    username: str
    ho: Optional[str] = None
    ten: Optional[str] = None
    quyen: Optional[str] = None
    dienthoai: Optional[str] = None
    diachi: Optional[str] = None
    trangthai: Optional[str] = None

    class Config:
        orm_mode = True
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

# API forgot-password
@app.put("/forgot-password/{username}", response_model=UserResponse)
def update_password(username: str, passwords: PasswordUpdate, db: Session = Depends(get_db)):
    # Lấy thông tin người dùng từ cơ sở dữ liệu
    db_user = db.query(User).filter(User.username == username).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Kiểm tra mật khẩu cũ
    if db_user.password != passwords.oldpassword:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    
    # Cập nhật mật khẩu mới
    db_user.password = passwords.newpassword
    
    # Commit và refresh dữ liệu người dùng
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
    
    query = db.query(Vehicle).order_by(Vehicle.createdAt.desc())

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
    
    for vehicle in vehicles:
        if vehicle.image_path_cam_truoc == "string":
            vehicle.image_path_cam_truoc = ""
        if vehicle.image_path_cam_sau == "string":
            vehicle.image_path_cam_sau = ""

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
    # Chuyển đổi đường dẫn host thành đường dẫn container
    container_path = image_path.replace(
        "/home/hello/project/be_server/app/images", 
        "/app/images"
    )

    print("container_pathcontainer_path", container_path)
    
    # Kiểm tra nếu tệp tồn tại trong container
    if not os.path.isfile(container_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # Trả về hình ảnh
    return FileResponse(container_path)

def get_sql_db():
    sql_server_db = SessionLocalSQLServer()
    try:
        yield sql_server_db
    finally:
        sql_server_db.close()

def check_and_save_vehicle_cam_truoc(vehicle, db: Session, current_time: datetime):
    # Lấy 10 phương tiện gần đây nhất
    vehicles = db.query(Vehicle).order_by(Vehicle.createdAt.desc()).limit(10).all()
    print("call2vehicles", [str(vehicle) for vehicle in vehicles])

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

    if any((current_time - vehicle.createdAt).total_seconds() < 120 for vehicle in vehicles):
        print(f"CAM Truoc Not created because exist in 120 seconds va direction ={vehicle.direction}")
        return {"message": f"CAM Truoc Not created because exist in 120 seconds va direction ={vehicle.direction}"}

    # Kiểm tra thời gian chênh lệch và các điều kiện khác
    if all((current_time - vehicle.createdAt).total_seconds() > 180 for vehicle in vehicles):
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

from sqlalchemy import text

def check_and_save_vehicle_cam_sau(vehicle, db: Session, current_time: datetime):
    # Lấy 10 phương tiện gần đây nhất
    db.execute(text("LOCK TABLE vehicles IN ACCESS EXCLUSIVE MODE"))
    vehicles = db.query(Vehicle).order_by(Vehicle.createdAt.desc()).limit(10).all()
    print("call2vehicles", [str(vehicle) for vehicle in vehicles])

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
    
    if any((current_time - vehicle.createdAt).total_seconds() < 120 for vehicle in vehicles):
        print(f"CAM SAU Not created because exist in 120 seconds va direction ={vehicle.direction}")
        return {"message": f"CAM SAU Not created because exist in 120 seconds va direction ={vehicle.direction}"}    
    
    # Kiểm tra thời gian chênh lệch và các điều kiện khác
    if all((current_time - vehicle.createdAt).total_seconds() > 180 for vehicle in vehicles):
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
    current_time_vn = datetime.utcnow() + timedelta(hours=7)
    print("current_time_vn_truoc=", current_time_vn)
    # Kiểm tra nếu thời gian từ 0h đến 5h sáng
    # if 0 <= current_time_vn.hour < 5:
    #     return {"message": "Không được lưu phương tiện trong khoảng từ 0h đến 5h sáng (giờ Việt Nam)"}
    
    # print("current_time_vn_sau=", current_time_vn)
    
    current_time = vehicle.createdAt or datetime.utcnow()
    print("vehicleDTO=", vehicle)
    # Gọi hàm kiểm tra và lưu phương tiện
    if vehicle.trackIdCamTruoc is not None:
        result = check_and_save_vehicle_cam_truoc(vehicle, db, current_time)
    
    # Kiểm tra nếu trackIdCamSau tồn tại, gọi check_and_save_vehicle_cam_sau
    if vehicle.trackIdCamSau is not None:
        print("call123")
        result = check_and_save_vehicle_cam_sau(vehicle, db, current_time)
    
    return result
        
@app.post("/register-new/")
def register_user(user: UserNewCreate, db: Session = Depends(get_sql_db)):
    # Kiểm tra xem username đã tồn tại hay chưa
    db_user = db.query(UserNew).filter(UserNew.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Tạo người dùng mới và lưu vào cơ sở dữ liệu
    new_user = UserNew(
        username=user.username,
        password=user.password,
        ho=user.ho,
        ten=user.ten,
        quyen=user.quyen,
        dienthoai=user.dienthoai,
        diachi=user.diachi,
        trangthai=user.trangthai
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "username": new_user.username}


# API Cập nhật thông tin người dùng
@app.put("/update-user-new/{user_id}", response_model=UserNewResponse)
def update_user(user_id: int, user: UserNewCreate, db: Session = Depends(get_sql_db)):
    db_user = db.query(UserNew).filter(UserNew.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cập nhật các trường có trong request
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# API Đăng nhập người dùng
@app.post("/login-new/")
def login_user(user: UserNewCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    print("db_user", db_user)
    if not db_user or db_user.password != user.password:
       raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # if user.password == "123456aA*" and user.username == "admin":
    #     return {"message": "Login successful", "username": user.username}
    
    # raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful", "username": db_user.username}

@app.get("/phieu_nhap")
def get_phieu_nhap(
    page: int = Query(1, ge=1),  # Số trang, bắt đầu từ 1
    size: int = Query(10, ge=1),  # Kích thước mỗi trang
    sophieu: Optional[str] = None,  # Bộ lọc theo số phiếu
    bienso: Optional[str] = None,  # Bộ lọc theo biển số
    loaihinh: Optional[str] = None,  # Bộ lọc theo loại hình
    ngay: Optional[str] = None,  # Bộ lọc theo ngày (format: YYYY-MM-DD)
    sql_server_db: Session = Depends(get_sql_db)
):
    query = sql_server_db.query(PhieuNhap)

    # Áp dụng bộ lọc
    if sophieu:
        query = query.filter(func.trim(PhieuNhap.sophieu).like(f"%{sophieu.strip()}%"))
    if bienso:
        query = query.filter(func.trim(PhieuNhap.bienso).like(f"%{bienso.strip()}%"))
    if loaihinh:
        query = query.filter(func.trim(PhieuNhap.loaihinh).like(f"%{loaihinh.strip()}%"))
    if ngay:
        try:
            # Parse `ngay` để lấy khoảng thời gian từ 00:00:00 đến 23:59:59
            start_date = datetime.strptime(ngay, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(PhieuNhap.ngay.between(start_date, end_date))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")


    # Tính tổng số mục
    total = query.count()

    # Áp dụng phân trang
    items = query.order_by(PhieuNhap.ngaytao.desc()).offset((page - 1) * size).limit(size).all()

    total_nhap = query.filter(func.trim(PhieuNhap.loaihinh).like("NHAP")).with_entities(func.sum(PhieuNhap.canlan1 - PhieuNhap.canlan2)).scalar() or 0
    total_xuat = (
    query.filter(
        func.trim(PhieuNhap.loaihinh).like("XUAT"),  # Chỉ lấy loại hình XUAT
        PhieuNhap.canlan2 != 0  # Chỉ tính nếu canlan2 khác 0
    )
    .with_entities(func.sum(PhieuNhap.canlan2 - PhieuNhap.canlan1))
    .scalar()
    ) or 0
    total_thue = query.filter(func.trim(PhieuNhap.loaihinh).like("CANTHUE")).with_entities(func.sum(PhieuNhap.canlan1)).scalar() or 0

    print("total_xuat", total_xuat)
    # Chuẩn bị response
    results = []
    for item in items:
        # Tính `kl_hang`
        kl_hang = 0
        if item.loaihinh.strip().upper() == "CANTHUE":
            kl_hang = item.canlan1 or 0
        elif item.loaihinh.strip().upper() == "NHAP":
            kl_hang = (item.canlan1 or 0) - (item.canlan2 or 0)
        elif item.loaihinh.strip().upper() == "XUAT":
            kl_hang = (item.canlan2 or 0) - (item.canlan1 or 0)

        # Tính `thanh_tien`
        try:
            dongia = float(item.dongia or 0)
        except ValueError:
            dongia = 0
        thanh_tien = dongia * kl_hang/1000

        # Thêm vào kết quả
        results.append({
            "id": item.id,
            "sophieu": item.sophieu,
            "ngay": item.ngay,
            "bienso": item.bienso,
            "taixe": item.taixe,
            "loaihinh": item.loaihinh,
            "canlan1": item.canlan1,
            "canlan2": item.canlan2,
            "giovao": item.giovao,
            "giora": item.giora,
            "loaihang": item.loaihang,
            "hopdong": item.hopdong,
            "ghichu": item.ghichu,
            "ngaytao": item.ngaytao,
            "nguoitao": item.nguoitao,
            "ngaycapnhat": item.ngaycapnhat,
            "nguoicapnhat": item.nguoicapnhat,
            "logChinhSua": item.logChinhSua,
            "idThe": item.idThe,
            "dongia": item.dongia,
            "is_thu_cong": item.is_thu_cong,
            "kl_hang": kl_hang,  # Thêm `kl_hang`
            "thanh_tien": thanh_tien  # Thêm `thanh_tien`
        })

    return {
        "all_nhap": total_nhap,  # Tổng kl_hang cho NHAP
        "all_xuat": total_xuat,  # Tổng kl_hang cho XUAT
        "all_thue": total_thue,   # Tổng kl_hang cho CANTHUE
        "total": total,
        "page": page,
        "size": size,
        "items": results
    }

@app.post("/create-phieu-nhap", response_model=PhieuNhapResponse)
def create_phieu_nhap(
    payload: PhieuNhapCreate,  # The DTO for request body
    sql_server_db: Session = Depends(get_sql_db),  # Dependency for DB session
):
    from sqlalchemy.sql import func

    # Get the current time for `ngaytao` and `ngaycapnhat`
    now = datetime.utcnow() + timedelta(hours=7)

    # Get the latest record in the table
    latest_phieu = (
        sql_server_db.query(PhieuNhap)
        .order_by(PhieuNhap.id.desc())  # Replace `id` with the actual primary key if different
        .first()
    )

    # Determine the new `sophieu`
    if latest_phieu and latest_phieu.sophieu.startswith("TC_000"):
        try:
            # Extract the number part from the existing `sophieu`
            latest_number = int(latest_phieu.sophieu.split("_")[1])
            new_number = latest_number + 1
        except (ValueError, IndexError):
            # Handle cases where the split fails or the number isn't valid
            new_number = latest_phieu.id + 1
    else:
        # If no valid latest `sophieu` exists, use "TC_000" + (latest ID + 1)
        new_number = (latest_phieu.id + 1) if latest_phieu else 1

    # Create the new `sophieu`
    new_sophieu = f"TC_000{new_number}"

    # Create a new PhieuNhap instance
    phieu_nhap = PhieuNhap(
        sophieu=new_sophieu,
        ngay=now,
        bienso=payload.bienso,
        taixe=payload.taixe,
        loaihinh=payload.loaihinh,
        canlan1=payload.canlan1,
        canlan2=payload.canlan2, 
        giovao=payload.giovao,
        giora=payload.giora, 
        loaihang=payload.loaihang,
        hopdong=payload.hopdong,
        ghichu=payload.ghichu,
        dongia=payload.dongia * 1000,
        is_thu_cong=True,
        ngaytao=now,
        nguoitao=payload.nguoitao,  # Set creator from DTO
        ngaycapnhat=now,
        nguoicapnhat=payload.nguoitao,  # Set last updater from DTO (same as creator initially)
    )
    # Add the new record to the database
    try:
        # Add the new record to the database
        sql_server_db.add(phieu_nhap)
        sql_server_db.commit()
        sql_server_db.refresh(phieu_nhap)
    except Exception as e:  # Catch all exceptions
        sql_server_db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail="Database error occurred")
    # Return the created PhieuNhap as a response
    return phieu_nhap


@app.put("/edit-phieu-nhap/{phieu_nhap_id}", response_model=PhieuNhapResponse)
def edit_phieu_nhap(
    phieu_nhap_id: int,
    payload: PhieuNhapUpdate,  # Use the updated DTO
    sql_server_db: Session = Depends(get_sql_db),
):
    try:
        # Find the existing PhieuNhap record
        phieu_nhap = sql_server_db.query(PhieuNhap).filter(PhieuNhap.id == phieu_nhap_id).first()
        if not phieu_nhap:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")

        print("call1", payload)
        # Update fields if present in payload
        phieu_nhap.sophieu = payload.sophieu or phieu_nhap.sophieu
        phieu_nhap.ngay = payload.ngay or phieu_nhap.ngay
        phieu_nhap.bienso = payload.bienso or phieu_nhap.bienso
        phieu_nhap.taixe = payload.taixe or phieu_nhap.taixe
        phieu_nhap.loaihinh = payload.loaihinh or phieu_nhap.loaihinh
        phieu_nhap.canlan1 = payload.canlan1 or phieu_nhap.canlan1
        phieu_nhap.canlan2 = payload.canlan2 or phieu_nhap.canlan2
        phieu_nhap.giovao = payload.giovao or phieu_nhap.giovao
        phieu_nhap.giora = payload.giora or phieu_nhap.giora
        phieu_nhap.loaihang = payload.loaihang or phieu_nhap.loaihang
        phieu_nhap.hopdong = payload.hopdong or phieu_nhap.hopdong
        phieu_nhap.ghichu = payload.ghichu or phieu_nhap.ghichu
        phieu_nhap.dongia = payload.dongia or phieu_nhap.dongia
        phieu_nhap.is_thu_cong = payload.is_thu_cong if payload.is_thu_cong is not None else phieu_nhap.is_thu_cong

        print("call2", phieu_nhap)

        # Set the updated_by field for the last updater
        if payload.nguoicapnhat:
            phieu_nhap.nguoicapnhat = payload.nguoicapnhat  # Update 'nguoicapnhat'
        phieu_nhap.ngaycapnhat = datetime.utcnow()  # Update 'ngaycapnhat'

        print("call3", phieu_nhap)

        # Commit the changes to the database
        sql_server_db.commit()
        sql_server_db.refresh(phieu_nhap)

        # Return the updated PhieuNhap as a response
        return phieu_nhap

    except Exception as e:
        sql_server_db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/xoa-phieu-nhap/{phieu_nhap_id}")
def delete_phieu_nhap(
    phieu_nhap_id: int,
    nguoi_xoa: str,  # Getting user from the request body
    sql_server_db: Session = Depends(get_sql_db),
):
    try:
        # Find the PhieuNhap record to delete
        phieu_nhap = sql_server_db.query(PhieuNhap).filter(PhieuNhap.id == phieu_nhap_id).first()
        if not phieu_nhap:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")

        # Log the deletion action
        print(f"User '{nguoi_xoa}' đã xóa phiếu nhập ID: {phieu_nhap_id}")

        # Delete the PhieuNhap record
        sql_server_db.delete(phieu_nhap)
        sql_server_db.commit()

        return {"detail": "Đã xóa phiếu nhập thành công."}

    except Exception as e:
        sql_server_db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/loai-hinh")
def get_list_loai_hinh(sql_server_db: Session = Depends(get_sql_db)):
    query = sql_server_db.query(tblLoaiHinh)
    items = query.all()
    return {"items": items}

@app.get("/loai-hang")
def get_list_dm_hang(sql_server_db: Session = Depends(get_sql_db)):
    query = sql_server_db.query(tblDmHang)
    items = query.all()
    return {"items": items}

@app.get("/khach-hang")
def get_list_khach_hang(sql_server_db: Session = Depends(get_sql_db)):
    query = sql_server_db.query(tblDmKH)
    items = query.all()
    return {"items": items}

@app.get("/khach-hang/{id}")
def get_khach_hang_by_id(id: int, sql_server_db: Session = Depends(get_sql_db)):
    khach_hang = sql_server_db.query(tblDmKH).filter(tblDmKH.Id == id).first()
    if not khach_hang:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    return khach_hang

@app.get("/loai-hang/{mahang}")
def get_hang_by_mahang(mahang: str, sql_server_db: Session = Depends(get_sql_db)):
    hang = sql_server_db.query(tblDmHang).filter(tblDmHang.mahang == mahang).first()
    if not hang:
        raise HTTPException(status_code=404, detail="Không tìm thấy hàng")
    return hang

@app.get("/loai-hinh/{ma}")
def get_loai_hinh_by_ma(ma: str, sql_server_db: Session = Depends(get_sql_db)):
    loai_hinh = sql_server_db.query(tblLoaiHinh).filter(tblLoaiHinh.ma == ma).first()
    if not loai_hinh:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại hình")
    return loai_hinh

@app.get("/monitor-phieu-nhap")
def monitor_phieu_nhap(sql_db: Session = Depends(get_sql_db), db: Session = Depends(get_db)):
    # Lấy bản ghi từ bảng PhieuNhap
    phieu_nhap = sql_db.query(PhieuNhap).order_by(PhieuNhap.id.desc()).first()
    if not phieu_nhap:
        return {"message": "PhieuNhap not found"}
    
    print("phieu_nhap", phieu_nhap)

    # Thêm 7 giờ vào giớ phát hành và giờ vào
    if phieu_nhap.giora:
        phieu_nhap.giora = phieu_nhap.giora + timedelta(hours=7)
        print("phieu_nhap.giora after adding 7 hours:", phieu_nhap.giora)

    if phieu_nhap.giovao:
        phieu_nhap.giovao = phieu_nhap.giovao + timedelta(hours=7)
        print("phieu_nhap.giovao after adding 7 hours:", phieu_nhap.giovao)

    # Lấy 3 bản ghi gần nhất từ Vehicle mà is_checked != True
    recent_vehicles = db.query(Vehicle).order_by(Vehicle.createdAt.desc()).limit(3).all()

    # Kiểm tra `giora` so với các bản ghi trong Vehicle (chỉ kiểm tra các Vehicle chưa được đánh dấu là True)
    if phieu_nhap.giora:
        print("phieu_nhap.giora=", phieu_nhap.giora)
        for vehicle in recent_vehicles:
            if abs((phieu_nhap.giora - vehicle.createdAt).total_seconds()) < 120 and vehicle.is_checked != True:
                print("phieu_nhap.giora<120=", phieu_nhap.giora)
                vehicle.direction = "ra"
                vehicle.is_checked = True  # Đánh dấu là đã kiểm tra
                db.commit()
                return {"message": f"Updated Vehicle ID {vehicle.id} direction to 'ra', marked as checked"}

    # Kiểm tra `giovao` so với các bản ghi trong Vehicle (chỉ kiểm tra các Vehicle chưa được đánh dấu là True)
    if phieu_nhap.giovao:
        print("phieu_nhap.giovao=", phieu_nhap.giovao)
        for vehicle in recent_vehicles:
            if abs((phieu_nhap.giovao - vehicle.createdAt).total_seconds()) < 120 and vehicle.is_checked != True:
                print("phieu_nhap.giovao<120=", phieu_nhap.giovao)
                vehicle.direction = "vao"
                vehicle.is_checked = True  # Đánh dấu là đã kiểm tra
                db.commit()
                return {"message": f"Updated Vehicle ID {vehicle.id} direction to 'vao', marked as checked"}

    # Nếu không có bản ghi nào thỏa mãn
    return {"message": "No matching Vehicle records found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.112", port=8000, log_level="info", reload=True)
