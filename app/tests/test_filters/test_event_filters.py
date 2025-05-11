import pytest
from datetime import timedelta
from django.utils import timezone
from events.filters import EventFilter
from tests.factories import EventFactory


@pytest.mark.django_db
class TestEventFilter:
    def test_location_filter(self):
        EventFactory(location='New York')
        EventFactory(location='Los Angeles')

        qs = EventFilter({'location': 'new'}).qs
        assert qs.count() == 1
        assert qs.first().location == 'New York'

    def test_status_filter(self):
        EventFactory(status='upcoming')
        EventFactory(status='completed')

        qs = EventFilter({'status': 'upcoming'}).qs
        assert qs.count() == 1
        assert qs.first().status == 'upcoming'

    def test_date_filters(self):
        now = timezone.now()
        EventFactory(start_time=now - timedelta(days=1))
        EventFactory(start_time=now + timedelta(days=1))

        qs = EventFilter({'start_date': now.isoformat()}).qs
        assert qs.count() == 1
        assert qs.first().start_time > now
