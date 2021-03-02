from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from typing import List, Union
from sqlalchemy import or_
from sqlalchemy_serializer import SerializerMixin


class User(UserMixin, db.Model):   # User inherits from db.Model, a base class for all models from Flask-sqlalchemy
    id = db.Column(db.Integer, primary_key=True)    # Fields are created as instances of the Column class, they take the field type as an argument
    email = db.Column(db.String(120), nullable=False, index=True, unique=True)  # By indexing a value you can find it more easily in the db
    first_name = db.Column(db.String(50), index=True, unique=False)
    last_name = db.Column(db.String(50), index=True, unique=False)
    password_hash = db.Column(db.String(128), nullable=True)
    draft = db.Column(db.Boolean, default=True)

    masterclasses_run = db.relationship('Masterclass', backref='instructor', lazy='dynamic')
    booked_masterclasses = db.relationship('MasterclassAttendee', backref='attendee', lazy='dynamic')

    def __repr__(self):
        return '<User {} {}>'.format(self.first_name, self.last_name)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_booked_masterclasses(self) -> List[Union['Masterclass', None]]:
        """
        Returns a list of masterclass objects which the user is an attendee of.
        """
        return [bm.masterclass for bm in self.booked_masterclasses]

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))


class MasterclassContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(500))
    category = db.Column(db.String(200))
    masterclass_instances = db.relationship('Masterclass', backref='content', lazy='dynamic')

    def __repr__(self):
        return '<MasterclassContent {}>'.format(self.name)


class Location(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    building = db.Column(db.String(50), index=True)
    street_number = db.Column(db.String(10)) # should keep numbers as strings unless going to do calculations?
    street_name = db.Column(db.String(100), index=True)
    town_or_city = db.Column(db.String(50), index=True)
    postcode = db.Column(db.String(8), index=True)  # A postcode in the UK can't have more than 8 characters inc. space
    name = db.Column(db.String, index=True)
    address = db.Column(db.String, index=True)
    maps_id = db.Column(db.String, index=True)
    masterclasses = db.relationship('Masterclass', backref='location', lazy='dynamic')

    def __repr__(self):
        return '<Location {}>'.format(self.name)

    @classmethod
    def return_existing_location_or_none(cls, query: str) -> Union[None, 'Location']:
        query = f'%{query}%'
        return Location.query.filter(or_(Location.name.ilike(query), Location.address.ilike(query))).all()


class Masterclass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True)
    max_attendees = db.Column(db.Integer)
    is_remote = db.Column(db.Boolean, index=True)
    remote_url = db.Column(db.String, index=True)
    remote_joining_instructions = db.Column(db.String, index=True)
    room = db.Column(db.String, index=True)
    floor = db.Column(db.String, index=True)
    building_instructions = db.Column(db.String, index=True)
    masterclass_content_id = db.Column(db.Integer, db.ForeignKey('masterclass_content.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    attendees = db.relationship('MasterclassAttendee', backref='masterclass')
    masterclass_content = db.relationship('MasterclassContent')
    draft = db.Column(db.Boolean, default=True)

    def remaining_spaces(self):
        return self.max_attendees - len(self.attendees)

    def set_location_details(self, data, is_remote):
        """
        Set location related fields for a masterclass.
        """
        if is_remote:
            self.set_remote_details(data)
        else:
            self.set_in_person_details(data)
        db.session.add(self)
        db.session.commit()
        return None

    def set_remote_details(self, data):
        self.remote_url = data["url"]
        if data["joining_instructions"]:
            self.remote_joining_instructions = data["joining_instructions"]
        self.is_remote = True
        return None

    def set_in_person_details(self, data):
        self.room = data["room"]
        self.floor = data["floor"]
        if data["building_instructions"]:
            self.building_instructions = data["building_instructions"]
        self.is_remote = False
        return None

    def create_new_masterclass_content_and_attach(self, content_name: str, content_description:str):
        new_content = MasterclassContent(name=content_name, description=content_description)
        self.masterclass_content = new_content
        db.session.add(self)
        db.session.commit()
        return None


class MasterclassAttendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attendee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    masterclass_id = db.Column(db.Integer, db.ForeignKey('masterclass.id'))
    
    
    @staticmethod 
    def is_attendee(attendee_id, masterclass_id):
        return bool(MasterclassAttendee.query.filter_by(masterclass_id = masterclass_id, attendee_id = attendee_id).first())
