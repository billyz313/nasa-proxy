from django.contrib.sites import requests
import logging
from logging.handlers import RotatingFileHandler
import datetime
import requests
import json
import dateutil.parser
from shapely.geometry import CAP_STYLE
from shapely.geometry import Polygon
from shapely_geojson import dumps

print(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


global PLANET_API_KEY
global session


def map_bounds(geometry):
    bounds = geometry.bounds
    return [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]


def p(data):
    print(json.dumps(data, indent=2))


def pick(dictionary, keys):
    return dict((k, dictionary.get(k)) for k in keys)


def feature_date(feature):
    return dateutil.parser.parse(feature['properties']['acquired']).strftime('%Y-%m-%d')


def distinct_date(features):
    dates = []
    result = []
    for feature in features:
        date = feature_date(feature)
        if not date in dates:
            dates.append(date)
            result.append(feature)
    return result


def date_filter(start, end):
    return {
        'type': 'DateRangeFilter',
        'field_name': 'acquired',
        'config': {
            'gte': start,
            'lt': end
        }
    }


def within_days_filter(feature, days):
    date = dateutil.parser.parse(feature['properties']['acquired'])
    start = (date - datetime.timedelta(days=days - 1)).strftime('%Y-%m-%d') + 'T00:00:00.000Z'
    end = (date + datetime.timedelta(days=days)).strftime('%Y-%m-%d') + 'T23:59:59.000Z'
    return date_filter(start, end)


def geometry_filter(geometry):
    return {
        'type': 'GeometryFilter',
        'field_name': 'geometry',
        'config': json.loads(dumps(geometry))
    }


def string_filter(field_name, strings):
    return {
        'type': 'StringInFilter',
        'field_name': field_name,
        'config': strings
    }


# The quality of a feature. Use clear_percent, with cloud_cover as a fallback
def quality(feature):
    properties = feature['properties']
    desired_quality = properties.get('clear_percent')  # clear_percent [0, 100] only exist on newer features
    if desired_quality is not None:
        return desired_quality
    else:
        # cloud_cover [0, 1] is really not very accurate and misses a lot of clouds.
        # Therefore we weight it a bit lower than clear_percent
        return (1 - properties['cloud_cover']) * 50


def search(item_types, filters, sort=False):
    and_filter = {
        'type': 'AndFilter',
        'config': filters
    }
    request = {
        'item_types': item_types,
        'filter': and_filter
    }

    def next_page(res_json):
        page_features = res_json.get('features')
        links = res_json.get('_links')
        if links and links['_next']:
            next_url = links['_next']
            page_res = requests.get(next_url, auth=(PLANET_API_KEY, ''))
            if page_res.status_code >= 400:
                raise ValueError('Error searching Planet. HTTP {}: {}'.format(page_res.status_code, page_res.reason))
            next_features = next_page(page_res.json())
            return page_features + next_features
        else:
            return page_features

    logger.debug(json.dumps(request))
    res = session.post('https://api.planet.com/data/v1/quick-search', json=request)

    logger.debug("after post")
    if res.status_code >= 400:
        raise ValueError('Error searching Planet. HTTP {}: {}'.format(res.status_code, res.reason))
    logger.debug("after returned")
    # There is unfortunately no ability to request sorted feature, so we have to get them all then sort them ourselves.
    # This means a whole lot of paging for long date-ranges. We might want to limit this...
    # We asked for them to implement the sorting, and they said they will.
    # We also asked for the ability to limit which metadata to return for each feature.
    features = next_page(res.json())
    if sort:
        return list(sorted(features, key=lambda f: quality(f), reverse=True))
    else:
        return features


def features_layer(features, name='Planet'):
    ids = [feature['properties']['item_type'] + ':' + feature['id'] for feature in features]
    # Request a tile URL for the feature ids. Unfortunately, we have no control over tile ordering in the resulting
    # tiles. This is something we asked for, so we can put best quality features at the top
    res = requests.post(
        'https://tiles0.planet.com/data/v1/layers',
        auth=(PLANET_API_KEY, ''),
        data={'ids': ', '.join(ids)}
    )
    if res.status_code >= 400:
        raise ValueError('Error creating Planet tile. HTTP {}: {}'.format(res.status_code, res.reason))
    layer_id = res.json()['name']
    layer_tiles = res.json()['tiles']
    return {"date": feature_date(features[0]), "layerID": layer_id, "url": layer_tiles}


# Add a layer with features similar to one the requested one.
def add_similar_features(feature, geometry, buffer):
    features = search(
        item_types=[feature['properties']['item_type']],
        filters=[
            geometry_filter(geometry.buffer(buffer, cap_style=CAP_STYLE.square)),
            # 0.5, cap_style=CAP_STYLE.square)),  # Close by
            within_days_filter(feature, 1),  # Same day
            string_filter('instrument', [feature['properties']['instrument']])  # Same instrument
        ],
        sort=False
    )
    name = feature_date(feature)
    return features_layer(features, name)


def get_planet_map_id(api_key, geometry, start, end=None, layer_count=1, item_types=['PSScene3Band', 'PSScene4Band'],
                      buffer=0.5, add_similar=True):
    logger.debug("getPlanetMapID")
    full_list = []
    global PLANET_API_KEY
    PLANET_API_KEY = api_key
    global session
    logger.debug("global session")
    session = requests.Session()
    session.auth = (PLANET_API_KEY, '')
    logger.debug("session authorized")
    if end is None:
        full_end = start + 'T23:59:59.000Z'
    else:
        full_end = end + 'T23:59:59.000Z'
    full_start = start + 'T00:00:00.000Z'
    logger.debug(str(Polygon(geometry)))
    logger.debug("fstart: " + full_start)
    logger.debug("fend: " + full_end)
    features = search(  # Scenes in date range, intersecting the geometry centroid, sorted by quality
        item_types=item_types,
        filters=[
            date_filter(full_start, full_end),  # date_filter(start, end),
            geometry_filter(Polygon(geometry)),
            string_filter('quality_category', ['standard'])
        ],
        sort=True
    )
    best_features = distinct_date(features)[0:layer_count]  # The best n features with distinct date, sorted by quality
    for feature in best_features[::-1]:  # Reverse the sorting and iterate
        # fullList.append(add_similar_features(feature, Polygon(geometry), buffer))
        if add_similar:
            logger.debug('Adding similar')
            full_list.append(add_similar_features(feature, Polygon(geometry), buffer))
        else:
            logger.debug('skipped similar')
            name = feature_date(feature)
            full_list.append(features_layer(features, name))
    if len(full_list) == 0:
        full_list.append({"date": "null", "layerID": "null", "url": "null"})
    return full_list
