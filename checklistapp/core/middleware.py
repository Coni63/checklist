from django.template.loader import render_to_string
from django.utils.deprecation import MiddlewareMixin


class HTMXMessagesMiddleware(MiddlewareMixin):
    """
    Middleware that add the message in the response body when using HTMX
    A js function then set the timeout if a hx-swap returns messages.

    Usual messages from Django are not compatible with HTMX
    """

    def process_response(self, request, response):
        # Cehck if the request is HTMX
        if request.headers.get("HX-Request") and hasattr(request, "_messages"):
            messages_list = list(request._messages)
            if messages_list:
                # add messages template to the body
                messages_html = render_to_string("messages.html", {}, request=request)
                if response.status_code == 200 and hasattr(response, "content"):
                    response.content = response.content + messages_html.encode()

        return response
