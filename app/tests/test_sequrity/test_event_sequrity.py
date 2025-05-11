import pytest

from tests.factories import EventFactory


@pytest.mark.django_db
class TestEventSecurity:
    def test_unauthorized_access(self, api_client):
        event = EventFactory()
        response = api_client.get(f'/api/events/{event.id}/')
        assert response.status_code == 200

        response = api_client.patch(
            f'/api/events/{event.id}/',
            data={'name': 'Hacker'}
        )
        assert response.status_code == 403
