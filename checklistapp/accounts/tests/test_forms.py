import pytest

from accounts.forms import BasicRegisterForm, UserEditForm

@pytest.mark.django_db
def test_register_form_valid():
    form = BasicRegisterForm(
        data={
            "username": "nicolas",
            "email": "nico@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
    )

    assert form.is_valid()
    user = form.save()
    assert user.email == "nico@test.com"


@pytest.mark.django_db
def test_register_form_password_mismatch():
    form = BasicRegisterForm(
        data={
            "username": "nico",
            "email": "nico@test.com",
            "password1": "pass1",
            "password2": "pass2",
        }
    )
    assert not form.is_valid()


@pytest.mark.django_db
def test_user_edit_form(user):
    form = UserEditForm(
        data={"first_name": "Nicolas", "last_name": "Dupont"},
        instance=user,
    )

    assert form.is_valid()
    form.save()

    user.refresh_from_db()
    assert user.first_name == "Nicolas"