import pytest

from flask import template_rendered
from contextlib import contextmanager
from app import create_app
from app import db as _db
from config import *
from app.models import MasterclassContent

@pytest.fixture
def test_app():
    app = create_app(TestConfig)
    yield app

@pytest.fixture
def client(test_app):
    with test_app.test_client() as client:
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


@pytest.fixture
def new_masterclass_content_data_category(db):
    mc = MasterclassContent(name='Introduction to R', description='This masterclass will give you a solid understanding of how to run queries using R.', category='Data')
    db.session.add(mc)
    db.session.commit()
    yield
    db.session.delete(mc)
    db.session.commit()

def test_login_not_required(client, db):
    rv = client.get('/')
    assert rv.status_code == 200


def test_login_required(login_required_client):
    rv = login_required_client.get('/')
    assert rv.status_code == 302

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
        print('hereeeeee', context)
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

@pytest.mark.parametrize('endpoint, data, expected_template',
(
    ('/choose-content', {'select-job-family': 'Data'}, 'create-masterclass/content/new-or-existing.html'),
    ('/choose-content/new-or-existing', {'which-masterclass': 'Introduction to R'}, 'index.html'),
    ('/choose-content/new-or-existing', {'which-masterclass': 'new masterclass'}, 'create-masterclass/content/create-new.html'),
    ('/choose-content/create-new', {'which-masterclass': 'An'}, 'index.html'),
))
def test_when_user_selects_create_new_masterclass_content_it_shows_masterclass_content_form(test_app, db, new_masterclass_content_data_category, endpoint, data, expected_template):
    with captured_templates(test_app) as templates:
        response = test_app.test_client().post(endpoint, data = data)
    assert response.status_code == 200
    assert len(templates) == 1
    template, context = templates[0]
    assert template.name == expected_template
   