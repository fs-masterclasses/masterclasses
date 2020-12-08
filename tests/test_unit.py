from app.models import MasterclassAttendee, User

import pytest


def test_get_booked_masterclasses_when_not_signed_up():
    """Test empty list is returned if a user has no booked masterclasses."""
    user = User()
    assert user.get_booked_masterclasses() == []


def test_get_booked_masterclasses(
    db,
    blank_session,
    test_masterclass,
    test_user,
):
    """Test list of masterclass objects returned if user has any booked."""
    ma = MasterclassAttendee(
      attendee_id=test_user.id,
      masterclass_id=test_masterclass.id)
    db.session.add(ma)
    db.session.commit()
    assert test_user.get_booked_masterclasses() == [test_masterclass]
