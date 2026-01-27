from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 1. USER TABLE (Login Info)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'manager', 'user'
    created_by = db.Column(db.String(50), default="system")

# 2. HUB TABLE (Locations)
class Hub(db.Model):
    id = db.Column(db.String(50), primary_key=True) # e.g. 'hub1'
    name = db.Column(db.String(100), nullable=False)
    traffic = db.Column(db.Integer, default=0)
    
    # Jab Hub delete hoga, toh uske cameras bhi delete ho jayenge
    cameras = db.relationship('Camera', backref='hub', cascade="all, delete")

# 3. CAMERA TABLE
class Camera(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(200), nullable=False)
    
    # Foreign Key: Ye camera kis Hub ka hai
    hub_id = db.Column(db.String(50), db.ForeignKey('hub.id'), nullable=False)
    
    light = db.Column(db.String(10), default="red")
    vehicles = db.Column(db.Integer, default=0)