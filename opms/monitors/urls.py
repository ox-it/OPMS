from django.conf.urls import patterns, url, include
from opms.monitors.views import *

urlpatterns = patterns('monitors.views',
    # Graphs generated by Stats
#    url(r'^url-scans/graph/url_by_time/(?P<url_id>\d{1,5}).png', graph_urlmonitoring_url),
    # Pages in url-scans
    url(r'^url-scans/url-(?P<url_id>\d{1,5})$', urlmonitoring_url, name="url-scans-url"),
    url(r'^url-scans/task-(?P<task_id>\d{1,5})$', urlmonitoring_task, name="url-scans-task"),
    url(r'^url-scans/$', urlmonitoring_summary, name="url-scans-summary"),

    # Pages in itunes
    url(r'^itunes/$', 'itu_home', name="itu-home"),
    url(r'^itunes/top-collections/$', 'itu_top_collections', name="itu-top-collections"),
    url(r'^itunes/top-items/$', 'itu_top_items', name="itu-top-items"),
    url(r'^itunes/collections/$', 'itu_collections', name="itu-collections"),
    url(r'^itunes/items/$', 'itu_items', name="itu-items"),
    url(r'^itunes/institutions/$', 'itu_institutions', name="itu-institutions"),
    url(r'^itunes/genres/$', 'itu_genres', name="itu-genres"),
    url(r'^itunes/scanlogs/$', 'itu_scanlogs', name="itu-scanlogs"),

    url(r'^itunes/collections/(?P<collection_id>\d+)/$', 'itu_collection', name="itu-collection"),
    url(r'^itunes/items/(?P<item_id>\d+)/$', 'itu_item', name="itu-item"),
    url(r'^itunes/institutions/(?P<institution_id>\d+)/$', 'itu_institution', name="itu-institution"),
    url(r'^itunes/institutions/(?P<institution_id>\d+)/collections/$', 'itu_institution_collections', name="itu-institution-collections"),
    url(r'^itunes/genres/(?P<genre_id>\d+)/$', 'itu_genre', name="itu-genre"),
    url(r'^itunes/scanlogs/(?P<scanlog_id>\d+)/$', 'itu_scanlog', name="itu-scanlog"),

    # Default page (aka, Monitors home)
    (r'^$', 'index'),
)