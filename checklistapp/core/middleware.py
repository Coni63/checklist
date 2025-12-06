from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string

class HTMXMessagesMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Vérifier si c'est une requête HTMX et s'il y a des messages
        if request.headers.get('HX-Request') and hasattr(request, '_messages'):
            messages_list = list(request._messages)
            if messages_list:
                # Rendre le template des messages
                messages_html = render_to_string('messages.html', {}, request=request)
                
                # Ajouter au contenu de la réponse
                if response.status_code == 200 and hasattr(response, 'content'):
                    response.content = response.content + messages_html.encode()
                    
        return response