from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):   # User inherits from db.Model, a base class for all models from Flask-sqlalchemy
    id = db.Column(db.Integer, primary_key=True)    # Fields are created as instances of the Column class, they take the field type as an argument
    email = db.Column(db.String(120), nullable=False, index=True, unique=True)  # By indexing a value you can find it more easily in the db
    first_name = db.Column(db.String(50), index=True, unique=False)
    last_name = db.Column(db.String(50), index=True, unique=False)
    password_hash = db.Column(db.String(128), nullable=False)
    masterclasses_run = db.relationship('Masterclass', backref='instructor', lazy='dynamic')
    booked_masterclasses = db.relationship('MasterclassAttendee', backref='attendee', lazy='dynamic')

    def __repr__(self):
        return '<User {} {}>'.format(self.first_name, self.last_name)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

class MasterclassContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(500))
    masterclass_instances = db.relationship('Masterclass', backref='content', lazy='dynamic')

    def __repr__(self):
        return '<MasterclassContent {}>'.format(self.name)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    building = db.Column(db.String(50), index=True)
    street_number = db.Column(db.String(10)) # should keep numbers as strings unless going to do calculations?
    street_name = db.Column(db.String(100), index=True)
    town_or_city = db.Column(db.String(50), index=True)
    postcode = db.Column(db.String(8), index=True)  # A postcode in the UK can't have more than 8 characters inc. space
    masterclasses = db.relationship('Masterclass', backref='location', lazy='dynamic')

    def __repr__(self):
        return '<Location {}>'.format(self.building)


class Masterclass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True)
    masterclass_content_id = db.Column(db.Integer, db.ForeignKey('masterclass_content.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class MasterclassAttendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attendee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    masterclass_id = db.Column(db.Integer, db.ForeignKey('masterclass.id'))
