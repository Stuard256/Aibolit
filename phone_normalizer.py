import re
from typing import List, Dict, Tuple

def process_phone_segments(segments: List[str]) -> Tuple[List[str], List[str]]:
    valid = []
    invalid = []
    current = []
    
    for seg in segments:
        clean_seg = re.sub(r'\D', '', seg)
        if not clean_seg:
            continue
            
        current.append(clean_seg)
        combined = ''.join(current)
        
        # Пытаемся определить возможный формат
        if len(combined) >= 12:
            # Слишком длинный номер
            invalid.append(''.join(current))
            current = []
        elif any([
            len(combined) == 12 and combined.startswith('375'),
            len(combined) == 11 and combined.startswith('80'),
            len(combined) in (9, 7, 6)
        ]):
            valid.append(combined)
            current = []
        elif len(combined) > 12:
            # Некорректная длина
            invalid.append(''.join(current))
            current = []
    
    # Обработка оставшихся цифр
    if current:
        combined = ''.join(current)
        if len(combined) in (12, 11, 9, 7, 6):
            valid.append(combined)
        else:
            invalid.append(combined)
    
    return valid, invalid

def convert_number(clean_num: str) -> str:
    if len(clean_num) == 12 and clean_num.startswith('375'):
        return clean_num
    if len(clean_num) == 11 and clean_num.startswith('80'):
        return '375' + clean_num[2:]
    if len(clean_num) == 9:
        return '375' + clean_num
    if len(clean_num) == 7:
        return '37529' + clean_num
    if len(clean_num) == 6:
        return '37517' + clean_num
    return None

def normalize_phone_v2(phone_str: str) -> Dict[str, List[str]]:
    if not phone_str:
        return {'valid': [], 'invalid': []}
    
    # Разделяем на сегменты и очищаем
    raw_segments = re.split(r'[\s,;|]+', phone_str.strip())
    cleaned_segments = [re.sub(r'\D', '', s) for s in raw_segments if s]
    
    # Обрабатываем сегменты
    valid_segments, invalid_segments = process_phone_segments(cleaned_segments)
    
    # Конвертируем номера
    valid_numbers = []
    seen = set()
    for num in valid_segments:
        converted = convert_number(num)
        if converted and len(converted) == 12 and converted.startswith('375'):
            if converted not in seen:
                valid_numbers.append(converted)
                seen.add(converted)
        else:
            invalid_segments.append(num)
    
    return {
        'valid': valid_numbers,
        'invalid': list(set(invalid_segments + invalid_segments))
    }