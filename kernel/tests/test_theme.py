"""Light/dark theme: the switch script and the markup it relies on."""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

from apps.authentication.factories import UserFactory
from kernel.constants.icons import ICON_SET

pytestmark = pytest.mark.django_db

THEME_JS = Path(settings.BASE_DIR) / 'kernel' / 'static' / 'js' / 'theme.js'


def _head(body):
    return body.split('</head>')[0]


def test_theme_script_runs_in_head_before_paint(client):
    head = _head(client.get(reverse('login')).content.decode())

    tag = re.search(r'<script [^>]*js/theme\.js[^>]*>', head)
    assert tag, 'theme.js must be in <head>'
    # Synchronous: deferred or async scripts run after the first paint.
    assert 'defer' not in tag.group(0) and 'async' not in tag.group(0)
    assert head.index('js/theme.js') < head.index('css/styles.css')


@pytest.mark.parametrize('signed_in', [False, True])
def test_pages_have_no_inline_scripts(client, signed_in):
    if signed_in:
        client.force_login(UserFactory())
    body = client.get(reverse('home' if signed_in else 'login')).content.decode()

    scripts = re.findall(r'<script\b[^>]*>', body)
    assert scripts
    assert all('src=' in tag for tag in scripts)
    assert not re.search(r'\son[a-z]+=', body), 'inline event handlers break the CSP'


def test_signed_in_users_get_the_theme_switch(client):
    client.force_login(UserFactory())

    body = client.get(reverse('home')).content.decode()

    switch = re.search(r'<button [^>]*data-theme-switch[^>]*>', body)
    assert switch and 'aria-label=' in switch.group(0)
    assert 'data-theme-icon' in body and 'data-theme-label' in body


def test_login_page_has_no_theme_switch(client):
    assert 'data-theme-switch' not in client.get(reverse('login')).content.decode()


def test_theme_icons_are_in_the_vendored_list():
    source = THEME_JS.read_text()

    for mapping in ('ICONS', 'FALLBACK_ICONS'):
        names = re.findall(r'"(\w+)"', re.search(rf'var {mapping} = \{{([^}}]*)\}}', source).group(1))
        assert len(names) == 3
        assert set(names) <= ICON_SET, mapping
