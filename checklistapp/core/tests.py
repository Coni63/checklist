import base64
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.utils import timezone

from .forms import Base64FileField  # Adaptez l'import

"""
Test templatetags
"""


@pytest.fixture
def render_template():
    def _render(text, context={}):
        # Remplacez 'votre_app' par le nom du fichier où sont vos tags
        t = Template("{% load custom_filters %}" + text)
        return t.render(Context(context))

    return _render


def test_smart_timesince_future(render_template):
    # Cas : Il y a 2 heures (doit afficher "2 hours ago")
    futur_date = timezone.now() + timedelta(hours=2)
    rendered = render_template("{{ date|smart_timesince }}", {"date": futur_date})
    expected_format = futur_date.strftime("%Y-%m-%d %H:%M:%S")
    assert rendered == expected_format


def test_smart_timesince_recent(render_template):
    # Cas : Il y a 2 heures (doit afficher "2 hours ago")
    past_date = timezone.now() - timedelta(hours=2)
    rendered = render_template("{{ date|smart_timesince }}", {"date": past_date})
    assert rendered == "2\xa0hours ago"


def test_smart_timesince_old(render_template):
    # Cas : Il y a 3 jours (doit afficher le format strftime)
    old_date = timezone.now() - timedelta(days=3)
    rendered = render_template("{{ date|smart_timesince }}", {"date": old_date})
    expected_format = old_date.strftime("%Y-%m-%d %H:%M:%S")
    assert rendered == expected_format


def test_url_with_query_tag(render_template):
    # Test ajout premier paramètre
    res1 = render_template("{% url_with_query '/home' 'tab=1' %}")
    assert res1 == "/home?tab=1"

    # Test ajout sur URL existante
    res2 = render_template("{% url_with_query '/search?q=test' 'page=2' %}")
    assert res2 == "/search?q=test&amp;page=2"


def test_get_item_filter(render_template):
    context = {"data": {"python": "cool", "java": "old"}}
    result = render_template("{{ data|get_item:'python' }}", context)
    assert result == "cool"

    result = render_template("{{ data|get_item:'ruby' }}", context)
    assert result == "None"


"""
Test form for B64
"""


def test_base64_file_field_success():
    field = Base64FileField()

    content = b"Hello Django"
    encoded_expected = base64.b64encode(content).decode("utf-8")

    uploaded_file = SimpleUploadedFile("test.txt", content)

    result = field.clean(uploaded_file)

    assert result == encoded_expected
    assert field.uploaded_filename == "test.txt"


def test_base64_file_field_too_large():
    field = Base64FileField()

    large_content = b"0" * (1024 * 101)
    uploaded_file = SimpleUploadedFile("big.txt", large_content)
    with pytest.raises(ValidationError) as excinfo:
        field.clean(uploaded_file)

    assert "File is too large, Maximum: 100 KB" in str(excinfo.value)


def test_base64_file_field_empty():
    field = Base64FileField(required=False)

    assert field.clean(None) is None
