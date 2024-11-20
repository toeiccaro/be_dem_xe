# Use the SQL Server 2022 image
FROM mcr.microsoft.com/mssql/server:2022-latest

# Cài đặt các công cụ cần thiết như curl, gnupg2 và mssql-tools (sqlcmd)
USER root

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-server.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools \
    && apt-get clean

# Chuyển lại về user mặc định của SQL Server
USER mssql

# Set môi trường và các biến
ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD=19921999aA*
ENV MSSQL_PID=Express

# Expose port mặc định cho SQL Server
EXPOSE 1433
