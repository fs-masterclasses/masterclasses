import pytest

from flask import session
from app import create_app
from app import db as _db
from config import *

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
def logged_in_user(test_client):
    with test_client:
        test_client.post(
            "main_bp.login", data={"email-address": "test@user.com", "password": "Password"}
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

def test_draft_masterclass_id_is_added_to_session(logged_in_user, blank_session):
    with logged_in_user.post('/create-masterclass'):
        assert session['draft_masterclass_id'] == 1
