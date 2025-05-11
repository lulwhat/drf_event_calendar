import pytest

from tests.factories import EventFactory, TagFactory


@pytest.mark.django_db
class TestSearchFlow:
    def test_search_with_filters(self, authenticated_client):
        # Create test data
        tag1 = TagFactory(name='backend')
        tag2 = TagFactory(name='frontend')

        mos_events = EventFactory.create_batch(2, location='Miami')
        for event in mos_events:
            event.tags.add(tag1)

        spb_events = EventFactory.create_batch(3, location='Philadelphia')
        for event in spb_events:
            event.tags.add(tag2)

        EventFactory(location='Dallas', available_seats=0)

        # Test different filters
        responses = [
            authenticated_client.get('/api/events/?location=Miami'),
            authenticated_client.get(f'/api/events/?tags={tag1.id}'),
            authenticated_client.get('/api/events/?min_available_seats=1'),
            authenticated_client.get('/api/events/?search=Philadelphia')
        ]

        # Check results
        assert responses[0].data['count'] == 2
        assert responses[1].data['count'] == 2
        assert responses[2].data['count'] == 5
        assert responses[3].data['count'] == 3
