from flask import url_for

from app import create_app
from app import db as _db
from app.models import Masterclass, MasterclassContent, User
from config import TestConfig

import pytest


@pytest.fixture(scope="session")
def test_app():
    app = create_app(TestConfig)
    yield app


@pytest.fixture(scope="session", autouse=True)
def test_client(test_app):

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = test_app.test_client()

    # Establish an application context before running the tests.
    ctx = test_app.test_request_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()


@pytest.fixture
def logged_in_user(test_client, db, test_user):
    with test_client:
        test_client.post(
            url_for("main_bp.login"),
            data={"email-address": "test@user.com", "password": "password"}
        )
        yield test_client
        test_client.get("main_bp.logout")


@pytest.fixture(scope="session")
def db(test_client):
    """
    This takes the FlaskClient object and applies it to the database.app attribute. Once this fixture is finished with, it drops everything in there
    """
    _db.app = test_client.application
    _db.create_all()

    yield _db

    _db.drop_all()


@pytest.fixture(scope="function", autouse=False)
def blank_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session_ = db.create_scoped_session(options=options)

    db.session = session_

    print("Yielding blank session")
    yield session_

    transaction.rollback()
    connection.close()
    session_.remove()
    print("Rolled back blank session")


@pytest.fixture
def test_user(db, blank_session):
    u = User(email='test@example.com')
    u.set_password('password')
    db.session.add(u)
    db.session.commit()
    yield u


@pytest.fixture()
def test_masterclass(db, blank_session):
    m = Masterclass(id=1)
    db.session.add(m)
    db.session.commit()
    yield m

@pytest.fixture
def test_content(db, blank_session):
    mc = MasterclassContent(id=1, name='Introduction to R', description='This masterclass will give you a solid understanding of how to run queries using R.', category='Data')
    db.session.add(mc)
    db.session.commit()
    yield mc
