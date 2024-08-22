import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Переменные окружения
host = os.getenv('DB_HOSTNAME')
port = os.getenv('DB_PORT')
dbname = os.getenv('DB_NAME')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

# Flask и SQLAlchemy настройки
app = Flask(__name__)
api = Api(app, doc='/api/shortener/docs')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Константы
SCHEMA = "shortener"
LINKS_TABLE_NAME = "links"
CLICKS_TABLE_NAME = "clicks"
