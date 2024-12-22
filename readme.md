#Run Server
uvicorn app.main:app --reload --host 192.168.1.112


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