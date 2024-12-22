# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from .db import Base
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  

    def __str__(self):
        return f"User ID: {self.id}, Username: {self.username}, Password: {self.password}"  # Log chi tiết

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    createdAt = Column(DateTime, default=datetime.utcnow, name="createdat")
    updatedAtByCamTruoc = Column(DateTime, name="updatedatbycamtruoc")
    updatedAtByCamSau = Column(DateTime, name="updatedatbycamsau")
    trackIdCamTruoc = Column(String, index=True, name="trackidcamtruoc", nullable=True)
    trackIdCamSau = Column(String, index=True, name="trackidcamsau", nullable=True)
    direction = Column(String)
    image_path_cam_truoc = Column(String, name="image_path_cam_truoc")
    image_path_cam_sau = Column(String, name="image_path_cam_sau")
    car_type = Column(String, name="car_type")  # Thêm cột car_type
    is_checked = Column(Boolean, nullable=True, default=False)  # Cột is_checked, mặc định là False

    def __str__(self):
        return (f"Vehicle ID: {self.id}, "
                f"Track ID Cam Truoc: {self.trackIdCamTruoc}, "
                f"Track ID Cam Sau: {self.trackIdCamSau}, "
                f"Created At: {self.createdAt}, "
                f"Updated By Cam Truoc: {self.updatedAtByCamTruoc}, "
                f"Updated By Cam Sau: {self.updatedAtByCamSau}, "
                f"Direction: {self.direction}, "
                f"Image Path Cam Truoc: {self.image_path_cam_truoc}, "
                f"Image Path Cam Sau: {self.image_path_cam_sau}, "
                f"Car Type: {self.car_type}, "
                f"Is Checked: {self.is_checked}")  # Thêm thông tin is_checked vào __str__

class PhieuNhap(Base):
    __tablename__ = "tblPhieuNhap"

    id = Column(Integer, primary_key=True, index=True)
    sophieu = Column(String)
    ngay = Column(DateTime)
    bienso = Column(String)
    taixe = Column(String)
    loaihinh = Column(String)
    canlan1 = Column(Float, nullable=True)
    canlan2 = Column(Float, nullable=True)
    giovao = Column(DateTime, nullable=True)
    giora = Column(DateTime, nullable=True)
    loaihang = Column(String)
    hopdong = Column(String)
    ghichu = Column(String)
    ngaytao = Column(DateTime)
    nguoitao = Column(String)
    ngaycapnhat = Column(DateTime, nullable=True)
    nguoicapnhat = Column(String, nullable=True)
    logChinhSua = Column(String, nullable=True)
    idThe = Column(String, nullable=True)
    dongia = Column(Float, nullable=True)
    is_thu_cong = Column(Boolean, nullable=False, name="isThuCong")  # Thêm cột này
    
    def as_dict(self):
        """
        Chuyển đổi một đối tượng `PhieuNhap` thành dictionary.
        """
        return {key: value for key, value in self.__dict__.items() if key != "_sa_instance_state"}


class UserNew(Base):
    __tablename__ = "tblUser"

    username = Column(String, primary_key=True, nullable=False)  # username không được NULL
    password = Column(String, nullable=False)  # password không được NULL
    ho = Column(String, nullable=True)  # Cho phép NULL
    ten = Column(String, nullable=True)  # Cho phép NULL
    quyen = Column(String, nullable=True)  # Cho phép NULL
    dienthoai = Column(String, nullable=True)  # Cho phép NULL
    diachi = Column(String, nullable=True)  # Cho phép NULL
    trangthai = Column(String, nullable=True)  # Cho phép NULL

    def __str__(self):
        return (
                f"Username: {self.username}, "
                f"Password: {self.password}, "
                f"Ho: {self.ho}, "
                f"Ten: {self.ten}, "
                f"Quyen: {self.quyen}, "
                f"Dienthoai: {self.dienthoai}, "
                f"Diachi: {self.diachi}, "
                f"Trangthai: {self.trangthai}")

class tblLoaiHinh(Base):
    __tablename__ = "tblLoaiHinh"

    ma = Column(String, primary_key=True)
    ten = Column(String)
    nguoitao = Column(String)
    ngaytao = Column(DateTime)

class tblDmHang(Base):
    __tablename__ = "tblDmHang"

    mahang = Column(String, primary_key=True)
    tenhang = Column(String)
    ghichu = Column(String, nullable=True)
    hoatdong = Column(Boolean, nullable=True)
    ngaytao = Column(DateTime)
    nguoitao = Column(String)
    tinhtapchat = Column(Boolean, nullable=True)
    nguoicapnhat = Column(String, nullable=True)
    ngaycapnhat = Column(DateTime, nullable=True)

class tblDmKH(Base):
    __tablename__ = "tblDmKH"

    Id = Column(Integer, primary_key=True)
    hoten = Column(String)
    diachi = Column(String, nullable=True)
    nguoitao = Column(String)
    ngaytao = Column(DateTime)
    nguoicapnhat = Column(String, nullable=True)
    ngaycapnhat = Column(DateTime, nullable=True)
