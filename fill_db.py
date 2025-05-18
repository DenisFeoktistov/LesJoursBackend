import json
import os
import django
from datetime import datetime
from django.utils import timezone
from django.utils.text import slugify
import random

# Добавляю импорт transliterate
try:
    from transliterate import translit
except ImportError:
    translit = None

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
        # Получаем адрес и контакты из parameters
        address = masterclass_data['parameters']['parameters']['Адрес'][0] if 'Адрес' in masterclass_data['parameters']['parameters'] else ''
        contacts = masterclass_data['parameters']['parameters']['Контакты'][0] if 'Контакты' in masterclass_data['parameters']['parameters'] else ''
        
        # Создаем мастер-класс
        masterclass = MasterClass.objects.create(
            name=masterclass_data['name'],
            short_description=masterclass_data['short_description'],
            long_description=masterclass_data['long_description'],
            start_price=masterclass_data['price']['start_price'],
            final_price=masterclass_data['price']['final_price'],
            bucket_link=masterclass_data['bucket_link'][0]['url'],
            location=address,  # Используем адрес из parameters
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

def regenerate_slugs():
    for mc in MasterClass.objects.all():
        name = mc.name
        # Транслитерируем, если возможно
        if translit:
            name_latin = translit(name, 'ru', reversed=True)
        else:
            name_latin = name
        new_slug = slugify(name_latin)
        mc.slug = new_slug
        mc.save()
    print("Слаги успешно перегенерированы!")

def randomize_scores():
    for mc in MasterClass.objects.all():
        mc.score_product_page = random.randint(0, 100)
        mc.save()
    print("Случайные значения score_product_page присвоены!")

def randomize_occupied_seats():
    for event in Event.objects.all():
        event.occupied_seats = random.randint(0, 5)
        event.save()
    print("Случайные значения occupied_seats присвоены!")

def update_age_parameters():
    for mc in MasterClass.objects.all():
        params = mc.parameters
        if 'parameters' in params and 'Возраст' in params['parameters']:
            age = params['parameters']['Возраст'][0]
            if age == '8+':
                params['parameters']['Возраст'] = ['6+']
            elif age == '14+':
                params['parameters']['Возраст'] = ['16+']
            elif age == '10+':
                params['parameters']['Возраст'] = ['12+']
            mc.parameters = params
            mc.save()
    print("Значения поля 'Возраст' в parameters обновлены!")

if __name__ == '__main__':
    print("Начинаем заполнение базы данных...")
    load_data()
    # randomize_occupied_seats()
    update_age_parameters()
    print("База данных успешно заполнена!") 