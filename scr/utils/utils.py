import random
import string
import logging

# Настройка логгирования
logger = logging.getLogger(__name__)

# Генерим рандомный урл
def generate_unique_short_url(link_model):
    characters = string.ascii_letters + string.digits
    while True:
        short_url = ''.join(random.choice(characters) for _ in range(6))
        if not link_model.query.filter_by(short_url=short_url).first():
            logger.info('Generated unique short URL: %s', short_url)
            return short_url

# Проверка валидности URL
def is_valid_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        logger.info('Valid URL provided: %s', url)
        return True
    else:
        logger.warning('Invalid URL provided: %s', url)
        return False
