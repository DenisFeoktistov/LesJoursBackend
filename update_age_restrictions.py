import os
import re
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesjours.settings')
django.setup()

from masterclasses.models import MasterClass

def extract_age_from_string(age_str):
    """Извлекает числовое значение возраста из строки вида '16+' или 'от 12 лет'"""
    if not age_str:
        return None
    
    # Поиск числового значения в строке
    match = re.search(r'(\d+)', age_str)
    if match:
        return int(match.group(1))
    return None

def update_age_restrictions():
    """Обновляет возрастные ограничения для всех мастер-классов на основе информации в parameters"""
    masterclasses = MasterClass.objects.all()
    updated_count = 0
    
    for mc in masterclasses:
        # Проверяем наличие параметров
        parameters = mc.parameters
        if not parameters or not isinstance(parameters, dict):
            print(f"Пропускаем мастер-класс {mc.id}: {mc.name} - отсутствуют параметры")
            continue
        
        # Получаем значение поля "Возраст" из параметров
        age_value = None
        
        # Проверяем структуру parameters
        if 'parameters' in parameters and isinstance(parameters['parameters'], dict):
            # Формат: {'parameters': {'Возраст': ['16+'], ...}, ...}
            if 'Возраст' in parameters['parameters'] and parameters['parameters']['Возраст']:
                age_value = parameters['parameters']['Возраст'][0]
        elif 'Возраст' in parameters and parameters['Возраст']:
            # Формат: {'Возраст': ['16+'], ...}
            if isinstance(parameters['Возраст'], list) and parameters['Возраст']:
                age_value = parameters['Возраст'][0]
            else:
                age_value = parameters['Возраст']
        
        if age_value:
            # Извлекаем числовое значение возраста
            age = extract_age_from_string(age_value)
            
            if age is not None and age != mc.age_restriction:
                print(f"Обновляем мастер-класс {mc.id}: {mc.name} - возраст с {mc.age_restriction} на {age}")
                mc.age_restriction = age
                mc.save(update_fields=['age_restriction'])
                updated_count += 1
            else:
                print(f"Мастер-класс {mc.id}: {mc.name} - возраст остался прежним: {mc.age_restriction}")
        else:
            print(f"Пропускаем мастер-класс {mc.id}: {mc.name} - не найдено поле 'Возраст'")
    
    print(f"\nОбновлено {updated_count} мастер-классов")

if __name__ == '__main__':
    update_age_restrictions() 