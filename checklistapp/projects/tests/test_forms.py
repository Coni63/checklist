import pytest

from projects.forms import ProjectCreationForm
from projects.models import Project


@pytest.mark.django_db
def test_project_creation_form_valid():
    """Test form with valid data"""
    form = ProjectCreationForm(
        data={
            "name": "New Project",
            "status": "active",
            "description": "Test description",
        }
    )

    assert form.is_valid()
    project = form.save()
    assert project.name == "New Project"
    assert project.status == "active"
    assert project.description == "Test description"


@pytest.mark.django_db
def test_project_creation_form_minimal_data():
    """Test form with minimal required data"""
    form = ProjectCreationForm(
        data={
            "name": "Minimal Project",
            "status": "active",
        }
    )

    assert form.is_valid()
    project = form.save()
    assert project.name == "Minimal Project"
    assert project.description == ""


@pytest.mark.django_db
def test_project_creation_form_empty_name():
    """Test form validation with empty name"""
    form = ProjectCreationForm(
        data={
            "name": "",
            "status": "active",
        }
    )

    assert not form.is_valid()
    assert "name" in form.errors


@pytest.mark.django_db
def test_project_creation_form_whitespace_only_name():
    """Test form validation with whitespace-only name"""
    form = ProjectCreationForm(
        data={
            "name": "   ",
            "status": "active",
        }
    )

    assert not form.is_valid()
    assert "name" in form.errors
    assert '<ul class="errorlist" id="id_name_error"><li>This field is required.</li></ul>' in str(form.errors["name"])


@pytest.mark.django_db
def test_project_creation_form_short_name():
    """Test form validation with name less than 3 characters"""
    form = ProjectCreationForm(
        data={
            "name": "AB",
            "status": "active",
        }
    )

    assert not form.is_valid()
    assert "name" in form.errors
    assert "at least 3 characters" in str(form.errors["name"])


@pytest.mark.django_db
def test_project_creation_form_duplicate_name():
    """Test form validation with duplicate name"""
    # Create existing project
    Project.objects.create(name="Existing Project")

    form = ProjectCreationForm(
        data={
            "name": "Existing Project",
            "status": "active",
        }
    )

    assert not form.is_valid()
    assert "name" in form.errors
    assert "already used" in str(form.errors["name"])


@pytest.mark.django_db
def test_project_creation_form_duplicate_name_case_insensitive():
    """Test form validation with duplicate name (case insensitive)"""
    # Create existing project
    Project.objects.create(name="Existing Project")

    form = ProjectCreationForm(
        data={
            "name": "existing project",
            "status": "active",
        }
    )

    assert not form.is_valid()
    assert "name" in form.errors
    assert "already used" in str(form.errors["name"])


@pytest.mark.django_db
def test_project_creation_form_name_trimmed():
    """Test that name is trimmed of whitespace"""
    form = ProjectCreationForm(
        data={
            "name": "  Test Project  ",
            "status": "active",
        }
    )

    assert form.is_valid()
    project = form.save()
    assert project.name == "Test Project"


@pytest.mark.django_db
def test_project_update_form_allows_same_name(project):
    """Test that update form allows keeping the same name"""
    form = ProjectCreationForm(
        data={
            "name": project.name,
            "status": "completed",
            "description": "Updated description",
        },
        instance=project,
    )

    assert form.is_valid()
    updated_project = form.save()
    assert updated_project.name == project.name
    assert updated_project.status == "completed"
    assert updated_project.description == "Updated description"


@pytest.mark.django_db
def test_project_creation_form_status_choices():
    """Test form with different status choices"""
    statuses = ["active", "completed", "archived"]

    for status in statuses:
        form = ProjectCreationForm(
            data={
                "name": f"Project {status}",
                "status": status,
            }
        )

        assert form.is_valid()
        project = form.save()
        assert project.status == status


@pytest.mark.django_db
def test_project_creation_form_invalid_status():
    """Test form with invalid status"""
    form = ProjectCreationForm(
        data={
            "name": "Test Project",
            "status": "invalid_status",
        }
    )

    assert not form.is_valid()
    assert "status" in form.errors


@pytest.mark.django_db
def test_project_creation_form_fields():
    """Test that form has the correct fields"""
    form = ProjectCreationForm()

    assert "name" in form.fields
    assert "status" in form.fields
    assert "description" in form.fields


@pytest.mark.django_db
def test_project_creation_form_widgets():
    """Test form widget attributes"""
    form = ProjectCreationForm()

    # Check name widget has placeholder and autofocus
    name_widget = form.fields["name"].widget
    assert "placeholder" in name_widget.attrs
    assert name_widget.attrs["autofocus"] is True

    # Check description widget
    description_widget = form.fields["description"].widget
    assert "placeholder" in description_widget.attrs
    assert description_widget.attrs["rows"] == 4


@pytest.mark.django_db
def test_project_creation_form_labels():
    """Test form field labels"""
    form = ProjectCreationForm()

    assert form.fields["name"].label == "Project Name"
    assert form.fields["description"].label == "Description"
    assert form.fields["status"].label == "Status"


@pytest.mark.django_db
def test_project_creation_form_help_texts():
    """Test form field help texts"""
    form = ProjectCreationForm()

    assert form.fields["name"].help_text == "Give your project a clear, descriptive name"
    assert form.fields["description"].help_text == "Add any notes or context about this project"
    assert form.fields["status"].help_text == "Set the current status of your project"
