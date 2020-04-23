import pytest

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
    session["candidate-id"] = 1

    yield testing_client  # this is where the testing happens!

    ctx.pop()

@pytest.fixture
def logged_in_user(test_client):
    with test_client:
        test_client.post(
            "main_bp.login", data={"email-address": "test@user.com", "password": "Password"}
        )
        yield
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


def test_login_not_required(test_client, db):
    rv = test_client.get('/')
    assert rv.status_code == 200


def test_login_required(logged_in_user, test_client):
    rv = test_client.get('/')
    assert rv.status_code == 200
