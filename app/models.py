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
    password = Column(String)  # Chú ý: Nên mã hóa mật khẩu trước khi lưu trữ!

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
                f"Car Type: {self.car_type}")  # Thêm thông tin car_type vào __str__ để hiển thị

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