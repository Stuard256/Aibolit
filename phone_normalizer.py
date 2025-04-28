import re
from typing import List, Dict, Tuple

def extract_digits(phone_str: str) -> str:
    """Извлекает только цифры из строки"""
    return re.sub(r'\D', '', phone_str)

def process_single_number(digits: str) -> Tuple[str, bool]:
    """Обрабатывает один номер, возвращает нормализованный номер и валидность"""
    length = len(digits)
    
    # Обработка коротких номеров (городских)
    if length == 6:
        return '375162' + digits, True  # Минск
    elif length == 7:
        return '37529' + digits, True  # Минск (7-значные)
    
    # Обработка мобильных номеров
    if digits.startswith('80') and length == 11:
        return '375' + digits[2:], True
    elif digits.startswith('375') and length == 12:
        return digits, True
    elif length == 9:
        return '375' + digits, True
    
    return digits, False

def normalize_phone_v3(phone_str: str) -> Dict[str, List[str]]:
    if not phone_str:
        return {'valid': [], 'invalid': []}
    
    raw_numbers = re.split(r'[\s,;/|\\-]+', phone_str.strip())
    
    valid_numbers = []
    invalid_numbers = []
    seen_numbers = set()
    
    for raw_num in raw_numbers:
        if not raw_num:
            continue
            
        digits = extract_digits(raw_num)
        if not digits:
            continue
            
        # Обрабатываем номер
        normalized, is_valid = process_single_number(digits)
        
        # Проверяем длину нормализованного номера
        if is_valid and len(normalized) == 12 and normalized.startswith('375'):
            if normalized not in seen_numbers:
                valid_numbers.append(normalized)
                seen_numbers.add(normalized)
        else:
            if digits not in seen_numbers:
                invalid_numbers.append(digits)
                seen_numbers.add(digits)
    
    return {
        'valid': valid_numbers,
        'invalid': invalid_numbers
    }