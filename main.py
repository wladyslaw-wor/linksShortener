from scr.core.config import app, api, db, SCHEMA, LINKS_TABLE_NAME, CLICKS_TABLE_NAME
from scr.utils.utils import generate_unique_short_url, is_valid_url
from sqlalchemy.exc import IntegrityError
from flask import request, redirect
from flask_restx import Resource, fields
import logging

# Настройка логгирования
logger = logging.getLogger(__name__)

# Определение моделей для Swagger
link_model = api.model('Link', {
    'url': fields.String(required=True, description='The original URL'),
    'short_url': fields.String(description='The shortened URL'),
    'created_at': fields.DateTime(description='The date the link was created'),
    'clicks_count': fields.Integer(description='The number of clicks on the shortened URL'),
})

click_model = api.model('Click', {
    'clicked_at': fields.DateTime(description='The time the click was made'),
    'user_agent': fields.String(description='The user agent of the click'),
    'referrer': fields.String(description='The referrer URL of the click'),
    'ip_address': fields.String(description='The IP address of the click'),
    'location': fields.String(description='The location of the click based on IP')
})

# Модели базы данных
class Link(db.Model):
    __tablename__ = LINKS_TABLE_NAME
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Click(db.Model):
    __tablename__ = CLICKS_TABLE_NAME
    __table_args__ = {'schema': SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey(f'{SCHEMA}.{LINKS_TABLE_NAME}.id'), nullable=False)
    clicked_at = db.Column(db.DateTime, server_default=db.func.now())
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    location = db.Column(db.Text)

# Создание сокращенной ссылки
@api.route('/api/shortener/shorten')
class ShortenURL(Resource):
    @api.expect(link_model, validate=True)
    @api.response(201, 'Link successfully shortened')
    def post(self):
        """Creates a shortened URL"""
        original_url = api.payload['url']
        if not is_valid_url(original_url):
            logger.warning('Invalid URL provided: %s', original_url)
            return {'error': 'Invalid URL'}, 400

        short_url = generate_unique_short_url(Link)
        logger.info('Generated short URL: %s', short_url)

        try:
            link = Link(original_url=original_url, short_url=short_url)
            db.session.add(link)
            db.session.commit()
            logger.info('Short URL successfully created for: %s', original_url)
        except IntegrityError:
            db.session.rollback()
            logger.error('Failed to generate unique short URL for: %s', original_url)
            return {'error': 'Failed to generate unique short URL'}, 500

        return {'short_url': request.host_url + short_url}, 201

# Переадресация по сокращенной ссылке
@api.route('/api/shortener/<string:short_url>')
class RedirectToURL(Resource):
    def get(self, short_url):
        """Redirects to the original URL"""
        link = Link.query.filter_by(short_url=short_url).first_or_404()
        logger.info('Redirecting short URL: %s to original URL: %s', short_url, link.original_url)

        click = Click(
            link_id=link.id,
            user_agent=request.headers.get('User-Agent'),
            referrer=request.referrer,
            ip_address=request.remote_addr,
            location=None  # Для геолокации по IP можно использовать сторонние API
        )
        db.session.add(click)
        db.session.commit()
        logger.info('Click recorded for short URL: %s', short_url)

        return redirect(link.original_url)

# Получение статистики по кликам
@api.route('/api/shortener/stats/<string:short_url>')
class URLStats(Resource):
    @api.marshal_list_with(click_model)
    def get(self, short_url):
        """Returns click statistics for a shortened URL"""
        link = Link.query.filter_by(short_url=short_url).first_or_404()
        clicks = Click.query.filter_by(link_id=link.id).all()

        stats = [{
            'clicked_at': click.clicked_at,
            'user_agent': click.user_agent,
            'referrer': click.referrer,
            'ip_address': click.ip_address,
            'location': click.location
        } for click in clicks]

        logger.info('Fetched click statistics for short URL: %s', short_url)
        return stats

# Получаем список ссылок
@api.route('/api/shortener/links')
class GetLinks(Resource):
    @api.marshal_list_with(link_model)
    def get(self):
        """Returns a list of all shortened URLs"""
        links = Link.query.all()
        all_links = [{
            'original_url': link.original_url,
            'short_url': request.host_url + link.short_url,
            'created_at': link.created_at,
            'clicks_count': Click.query.filter_by(link_id=link.id).count()
        } for link in links]

        logger.info('Fetched all shortened URLs')
        return all_links

# Редактирование ссылки
@api.route('/api/shortener/edit/<string:short_url>')
class EditLink(Resource):
    @api.expect(link_model, validate=True)
    @api.response(200, 'Link successfully updated')
    def put(self, short_url):
        """Edits the original URL for a shortened URL"""
        link = Link.query.filter_by(short_url=short_url).first_or_404()
        new_url = api.payload.get('url')

        if not new_url:
            logger.warning('No URL provided for updating short URL: %s', short_url)
            return {'error': 'No URL provided'}, 400

        link.original_url = new_url
        db.session.commit()
        logger.info('Updated short URL: %s with new URL: %s', short_url, new_url)

        return {
            'message': 'Link updated successfully',
            'short_url': request.host_url + link.short_url,
            'original_url': link.original_url
        }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = 8080
    app.run(debug=True, port=port)
