from __future__ import unicode_literals
import urllib.request
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def proxy_nasa_rss(request):
    callback_function_name = request.POST.get("callback", request.GET.get("callback", None))
    return get_http_response('https://www.nasa.gov/rss/dyn/aeronautics.rss', callback_function_name)


@csrf_exempt
def proxy_nasa_youtube(request):
    callback_function_name = request.POST.get("callback", request.GET.get("callback", None))
    return get_http_response('https://www.youtube.com/feeds/videos.xml?playlist_id=PLiuUQ9asub3Qq1AQRirDI-naOwo1H5gaB',
                             callback_function_name)


def get_http_response(url, callback):
    content_type = 'application/javascript'
    response = urllib.request.urlopen(url)
    xml_content = response.read()
    formatted_string = str(xml_content).replace("b'<", "'<").replace(r"\r\n", "").replace(r"\r", "").replace(
        r"\n", "").replace(r"\xe2\x80\x99s", "&#39;s").replace(r"\xe2\x80\x93", "-")
    if callback:
        return_value = str(callback) + str("(" + formatted_string + ")")
    else:
        return_value = str(formatted_string).replace("'<", "<").replace(r"</rss>'", r"</rss>")
        content_type = "application/xml"
    print(str(return_value))
    http_response = HttpResponse(str(return_value), content_type=content_type)
    http_response['Access-Control-Allow-Origin'] = '*'
    http_response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    http_response['Access-Control-Allow-Headers'] = 'Content-Type'
    return http_response
