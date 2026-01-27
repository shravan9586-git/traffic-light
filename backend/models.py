from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.String(50))
    login_time = db.Column(db.Float)

class Hub(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    traffic = db.Column(db.Integer, default=0)

class Camera(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    hub_id = db.Column(db.String(50), db.ForeignKey('hub.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(200), nullable=False)
    light = db.Column(db.String(10), default="red")
    vehicles = db.Column(db.Integer, default=0)