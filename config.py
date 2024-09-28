from dotenv import load_dotenv
from os import getenv
from app import app  # Import create_app function
load_dotenv()

app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['UPLOAD_FOLDER'] = 'static'
app.config['UPLOAD_PDF_FOLDER'] = 'static'