# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@192.168.1.112/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

SQL_SERVER_URL = "mssql+pyodbc://sa:19921999aA*@sqlserver_be/Scale?driver=ODBC+Driver+17+for+SQL+Server"
engine_sql_server = create_engine(SQL_SERVER_URL)
SessionLocalSQLServer = sessionmaker(autocommit=False, autoflush=False, bind=engine_sql_server)