from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponsePermanentRedirect
from django.conf import settings
from django.urls import is_valid_path
import re


class AppendOrRemoveSlashMiddleware(MiddlewareMixin):
    """
    Middleware для обработки URL с trailing slash и без него.
    Поддерживает все типы запросов (GET, POST, PUT, DELETE и т.д.)
    """
    
    def process_request(self, request):
        # Получаем URL-путь запроса
        path = request.path
        urlconf = getattr(request, 'urlconf', None)
        
        # Проверяем URL без слеша
        if not path.endswith('/'):
            path_with_slash = path + '/'
            if is_valid_path(path_with_slash, urlconf):
                # URL со слешем существует, но мы не будем перенаправлять
                # Вместо этого мы меняем URL запроса, чтобы он соответствовал пути со слешем
                request.path = request.path_info = path_with_slash
                return None
        
        # Проверяем URL со слешем
        elif path != '/' and path.endswith('/'):
            path_without_slash = path[:-1]
            if is_valid_path(path_without_slash, urlconf):
                # URL без слеша существует, но мы не будем перенаправлять
                # Вместо этого оставляем URL как есть со слешем
                return None
        
        return None

class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response["Access-Control-Allow-Headers"] = "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
        response["Access-Control-Expose-Headers"] = "Content-Length,Content-Range"
        return response 