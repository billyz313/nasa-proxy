from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('nasa_rss/', views.proxy_nasa_rss, name='nasa_rss'),
    path('nasa_youtube/', views.proxy_nasa_youtube, name='nasa_youtube'),
    path('get_planet_tile/', views.get_planet_tile, name='get_planet_tile'),
    path('aero_not/list/', views.aero_not_list, name='aero_not_list'),
    path('air_now/list/', views.air_now_list, name='air_now_list'),
    path('slicedfromcatalog/', views.air_quality_sliced_from_catalog, name='air_quality_sliced_from_catalog'),
    path('getData/', views.air_quality_get_data, name='air_quality_get_data'),
    path('getChartDataProcess/', views.get_chart_data_process, name='get_chart_data_process'),
    path('getLayerInfoStat/', views.get_layer_info_stat, name='get_layer_info_stat'),
    path('timeseriesmodeldata/', views.time_series_model_data, name='time_series_model_data'),

    path('dhm_station_data/', views.dhm_station_data, name='dhm_station_data'),
]
