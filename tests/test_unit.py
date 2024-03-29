from app.models import Masterclass, MasterclassAttendee, User

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
        attendee_id=test_user.id, masterclass_id=test_masterclass.id
    )
    db.session.add(ma)
    db.session.commit()
    assert test_user.get_booked_masterclasses() == [test_masterclass]


@pytest.mark.parametrize(
    "method, data, optional_field",
    (
        (
            "set_remote_details",
            {"url": "url.com", "joining_instructions": ""},
            "remote_joining_instructions",
        ),
        (
            "set_in_person_details",
            {"room": "1d", "floor": "1", "building_instructions": ""},
            "building_instructions",
        ),
    ),
)
def test_empty_optional_fields_set_as_none(
    db, blank_session, test_masterclass, data, method, optional_field
):
    """
    Tests that when an empty string is passed as the value of an optional
    model field on Masterclass, that field is set to none.
    """
    method = getattr(test_masterclass, method)
    method(data)
    assert getattr(test_masterclass, optional_field) is None
