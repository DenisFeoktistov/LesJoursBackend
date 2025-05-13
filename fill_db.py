import json
import os
import django
from datetime import datetime
from django.utils import timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesjours.settings')
django.setup()

from masterclasses.models import MasterClass, Event

def load_data():
    # Читаем JSON файл
    with open('data (1).json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Создаем мастер-классы
    for masterclass_data in data:
        # Создаем мастер-класс
        masterclass = MasterClass.objects.create(
            name=masterclass_data['name'],
            short_description=masterclass_data['short_description'],
            long_description=masterclass_data['long_description'],
            start_price=masterclass_data['price']['start_price'],
            final_price=masterclass_data['price']['final_price'],
            bucket_link=masterclass_data['bucket_link'][0]['url'],
            location=masterclass_data['location'],
            max_seats=masterclass_data['max_seats'],
            age_restriction=masterclass_data['age_restriction'],
            duration=masterclass_data['duration'],
            parameters=masterclass_data['parameters'],
            details=masterclass_data['details']
        )

        # Создаем события для мастер-класса
        for event_data in masterclass_data['events']:
            Event.objects.create(
                masterclass=masterclass,
                start_datetime=datetime.fromisoformat(event_data['start_datetime'].replace('Z', '+00:00')),
                end_datetime=datetime.fromisoformat(event_data['end_datetime'].replace('Z', '+00:00')),
                available_seats=event_data['available_seats'],
                occupied_seats=event_data['occupied_seats'],
                created_at=datetime.fromisoformat(event_data['created_at'].replace('Z', '+00:00'))
            )

if __name__ == '__main__':
    print("Начинаем заполнение базы данных...")
    load_data()
    print("База данных успешно заполнена!") 