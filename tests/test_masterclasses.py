import pytest

from app import create_app
from app import db as _db
from config import *


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client


@pytest.fixture
def login_required_client():
    app = create_app(TestLoginConfig)
    with app.test_client() as client:
        yield client


@pytest.fixture
def db(client):
    """
    This takes the FlaskClient object and applies it to the database.app attribute. Once this fixture is finished with, it drops everything in there
    """
    _db.app = client.application
    _db.create_all()

    yield _db

    _db.drop_all()


def test_login_not_required(client, db):
    rv = client.get('/')
    assert rv.status_code == 200


def test_login_required(login_required_client):
    rv = login_required_client.get('/')
    assert rv.status_code == 302


class TestRegister:
    def test_get(self, client):
        rv = client.get('/register')
        assert rv.status_code == 200
        assert b"Register for the site" in rv.data

    def test_post(self, client):
        pass
