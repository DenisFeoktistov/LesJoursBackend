from django_filters import rest_framework as filters
from ..models import MasterClass
from django.db import models


class MasterClassFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="final_price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="final_price", lookup_expr='lte')
    price_min = filters.NumberFilter(field_name="final_price", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="final_price", lookup_expr='lte')
    is_sale = filters.BooleanFilter(method='filter_has_discount')
    age = filters.MultipleChoiceFilter(
        choices=[(6, '6+'), (12, '12+'), (16, '16+')],
        field_name='age_restriction',
        method='filter_age_restrictions'
    )

    class Meta:
        model = MasterClass
        fields = ['min_price', 'max_price', 'price_min', 'price_max', 'is_sale', 'age']

    def filter_has_discount(self, queryset, name, value):
        if value is True:
            return queryset.filter(final_price__lt=models.F('start_price'))
        elif value is False:
            return queryset.filter(final_price=models.F('start_price'))
        return queryset

    def filter_age_restrictions(self, queryset, name, value):
        if not value:
            return queryset
            
        # Конвертируем значения в числа, если они переданы как строки
        valid_ages = []
        for age in value:
            try:
                if isinstance(age, str):
                    age = age.replace('+', '')
                valid_ages.append(int(age))
            except (ValueError, TypeError):
                pass
                
        if valid_ages:
            return queryset.filter(age_restriction__in=valid_ages)
            
        return queryset 