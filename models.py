from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    requests = db.relationship("Request", back_populates="user")
    feedbacks = db.relationship("Feedback", back_populates="user")

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    section = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.Date, nullable=False)
    author=db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', backref=db.backref('section', lazy=True))
    pdf_path = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String)
    requests = db.relationship("Request", back_populates="section")
    feedbacks = db.relationship("Feedback", back_populates="section")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.Date, nullable=False)
    sections = db.relationship("Section", back_populates="category")
    

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    return_date = db.Column(db.DateTime, nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)
    revoked = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String)
    
    # Define relationships
    user = db.relationship("User", back_populates="requests")
    section = db.relationship("Section", back_populates="requests")

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # Add a new column for rating
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Define relationships
    section = db.relationship('Section', back_populates='feedbacks')
    user = db.relationship('User', back_populates='feedbacks')



with app.app_context():
    db.create_all()
    admin_username = 'admin'
    admin = User.query.filter_by(username=admin_username).first()
    if not admin:
        admin_password = 'admin'  # Change this to a more secure password
        admin_name = 'Admin'  # Change this to the admin's name if needed
        admin = User(username=admin_username, password=admin_password, name=admin_name, is_admin=True)
        db.session.add(admin)
        db.session.commit()
