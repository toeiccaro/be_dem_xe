# Sử dụng image Python chính thức từ Docker Hub
FROM python:3.9-slim

# Cài đặt các phụ thuộc cho pyodbc và ODBC driver cho SQL Server
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    curl \
    gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy các file requirements.txt vào container
COPY requirements.txt /app/

# Cài đặt các thư viện cần thiết từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn của bạn vào container
COPY . /app/

# Mở cổng 8000 cho ứng dụng FastAPI
EXPOSE 8000

# Lệnh để chạy ứng dụng FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
