from __future__ import unicode_literals

import distutils
import json
import urllib.request
from .planet_utilities import get_planet_map_id
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import logging
from logging.handlers import RotatingFileHandler
import requests

print(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@csrf_exempt
def aero_not_list(request):
    return HttpResponse(
        json.dumps(
            json.load(
                urllib.request.urlopen('http://hkh-aqx.servirglobal.net/api/v1/location/source/aero_not/list/'))),
        content_type='application/json')


@csrf_exempt
def air_now_list(request):
    return HttpResponse(
        json.dumps(
            json.load(
                urllib.request.urlopen('http://hkh-aqx.servirglobal.net/api/v1/location/source/air_now/list/'))),
        content_type='application/json')


@csrf_exempt
def get_layer_info_stat(request):
    response = requests.post('http://smog.icimod.org/apps/airquality/getLayerInfoStat/', json=json.loads(request.body))
    return HttpResponse(response.content)


@csrf_exempt
def get_chart_data_process(request):
    response = requests.post('http://smog.icimod.org/apps/airquality/getChartDataProcess/', json=json.loads(request.body))
    return HttpResponse(response.content)


@csrf_exempt
def air_quality_sliced_from_catalog(request):
    post_data = request.POST
    response = requests.post('http://smog.icimod.org/apps/airquality/slicedfromcatalog/', data=post_data)
    return HttpResponse(response.content)


@csrf_exempt
def air_quality_get_data(request):
    post_data = request.POST
    response = requests.post('http://smog.icimod.org/apps/airquality/getData/', data=post_data)
    return HttpResponse(response.content)


@csrf_exempt
def proxy_nasa_rss(request):
    callback_function_name = request.POST.get("callback", request.GET.get("callback", None))
    return get_http_response('https://www.nasa.gov/rss/dyn/aeronautics.rss', callback_function_name)


@csrf_exempt
def proxy_nasa_youtube(request):
    callback_function_name = request.POST.get("callback", request.GET.get("callback", None))
    return get_http_response('https://www.youtube.com/feeds/videos.xml?playlist_id=PLiuUQ9asub3Qq1AQRirDI-naOwo1H5gaB',
                             callback_function_name)


@csrf_exempt
def get_planet_tile(request):
    logger.debug("get_planet_tile was called")
    try:
        request_json = ""
        if request.body:
            request_json = json.loads(request.body)
        if request_json:
            api_key = request_json.get('apiKey')
            geometry = request_json.get('geometry')
            start = request_json.get('dateFrom')
            end = request_json.get('dateTo', None)
            layer_count = request_json.get('layerCount', 1)
            item_types = request_json.get('itemTypes', ['PSScene'])
            buffer = int(request_json.get('buffer', 0.5))
            add_similar = bool(distutils.util.strtobool(request_json.get('addsimilar', 'True')))

            values = get_planet_map_id(api_key, geometry, start, end, layer_count, item_types, buffer, add_similar)

        else:
            api_key = request.POST.get("apiKey", request.GET.get("apiKey", None))
            geometry = request.POST.get("geometry", request.GET.get("geometry", None))
            start = request.POST.get("dateFrom", request.GET.get("dateFrom", None))
            end = request.POST.get("dateTo", request.GET.get("dateTo", None))
            layer_count = int(request.POST.get("layerCount", request.GET.get("layerCount", 1)))
            item_types = request.POST.get("itemTypes", request.GET.get("itemTypes", ['PSScene']))
            buffer = int(request.POST.get("buffer", request.GET.get("buffer", 0.5)))
            add_similar = bool(
                distutils.util.strtobool(request.POST.get("addsimilar", request.GET.get("addsimilar", "True"))))

            values = get_planet_map_id(api_key, json.loads(geometry), start, end, layer_count, item_types, buffer, add_similar)

    except Exception as e:
        values = {
            'errMsg': str(e)
        }
    return HttpResponse(json.dumps(values), content_type='application/json')


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
