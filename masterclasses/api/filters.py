from django_filters import rest_framework as filters
from ..models import MasterClass
from django.db import models


class MasterClassFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="final_price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="final_price", lookup_expr='lte')
    has_discount = filters.BooleanFilter(method='filter_has_discount')
    age_restrictions = filters.CharFilter(method='filter_age_restrictions')

    class Meta:
        model = MasterClass
        fields = ['min_price', 'max_price', 'has_discount', 'age_restrictions']

    def filter_has_discount(self, queryset, name, value):
        if value is True:
            return queryset.filter(final_price__lt=models.F('start_price'))
        elif value is False:
            return queryset.filter(final_price__gte=models.F('start_price'))
        # Если значение невалидно, возвращаем пустой queryset
        return queryset.none()

    def filter_age_restrictions(self, queryset, name, value):
        if not value:
            return queryset
        age_values = value.split(',')
        age_mapping = {
            '6+': 6,
            '12+': 12,
            '16+': 16,
            '6': 6,
            '12': 12,
            '16': 16
        }
        age_filters = []
        for age in age_values:
            age = age.strip()
            if age in age_mapping:
                age_filters.append(age_mapping[age])
            elif age.isdigit() and int(age) in (6, 12, 16):
                age_filters.append(int(age))
        if age_filters:
            return queryset.filter(age_restriction__in=age_filters)
        # Если невалидные значения — возвращаем пустой queryset
        return queryset.none() 