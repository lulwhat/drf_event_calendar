import django_filters

from events.models import Event, Tag


class EventFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__id',
        queryset=Tag.objects.all(),
        to_field_name='id',
        conjoined=True
    )
    location = django_filters.CharFilter(lookup_expr='icontains')
    min_available_seats = django_filters.NumberFilter(
        method='filter_available_seats'
    )
    max_available_seats = django_filters.NumberFilter(
        method='filter_available_seats'
    )
    start_date = django_filters.DateTimeFilter(field_name='start_time',
                                               lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='start_time',
                                             lookup_expr='lte')
    status = django_filters.ChoiceFilter(choices=Event.STATUS_CHOICES)
    organizer = django_filters.NumberFilter(field_name='organizer__id')

    class Meta:
        model = Event
        fields = [
            'location', 'status', 'organizer',
            'min_available_seats', 'max_available_seats',
            'start_date', 'end_date'
        ]

    def filter_available_seats(self, queryset, name, value):
        if name == 'min_available_seats':
            return queryset.filter(_available_seats_count__gte=value)
        elif name == 'max_available_seats':
            return queryset.filter(_available_seats_count__lte=value)
        return queryset
