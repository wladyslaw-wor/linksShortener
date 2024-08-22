import random
import string

# Генерим рандомный урл
def generate_unique_short_url(link_model):
    characters = string.ascii_letters + string.digits
    while True:
        short_url = ''.join(random.choice(characters) for _ in range(6))
        if not link_model.query.filter_by(short_url=short_url).first():
            return short_url

# Проверка валидности URL
def is_valid_url(url):
    return url.startswith('http://') or url.startswith('https://')
