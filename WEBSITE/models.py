from flask_login import UserMixin
from sqlalchemy.sql import func
from . import db


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime(timezone=True), default=func.now())
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    firstName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))
    password = db.Column(db.String(150))
    notes = db.relationship('Note')

class Beta(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    products = db.Column(db.String(150))
    water_level = db.Column(db.Float)
    water_apply = db.Column(db.Float)
    fertilizer = db.Column(db.Float)
    date_fertilize = db.Column(db.DateTime)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    position = db.Column(db.String(255))
    office = db.Column(db.String(255))
    age = db.Column(db.Integer)
    start_date = db.Column(db.DateTime)
    salary = db.Column(db.Float)
    label = db.Column(db.Float)  # Add this line to define the label column

