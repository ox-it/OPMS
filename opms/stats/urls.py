from django.conf.urls.defaults import *

urlpatterns = patterns('stats.views',
    # These URLS will all change!
    #(r'^report/pr/item/(?P<guid>.+)', 'pr_report3'),
    #(r'^report/pr/partial-guid/(?P<partial_guid>.+)', 'pr_report2'),
    #(r'^report/pr/(?P<sort_by>.*)', 'pr_report1'),

    # Pages in Stats
    (r'^report/summary/feeds/partial-guid/(?P<partial_guid>.+)', 'feed_detail'),
    (r'^report/summary/feeds/$', 'summary_feeds'),
    # Temp hack CC pages for PR
    (r'^report/summary/feeds-cc/partial-guid/(?P<partial_guid>.+)', 'feed_detail_cc'),
    (r'^report/summary/feeds-cc/$', 'summary_feeds_cc'),

    (r'^report/summary/items/(?P<guid>.+)$', 'item_detail'),
    (r'^report/summary/items/$', 'summary_items'),
    (r'^report/summary/$', 'summary_index'),

    # Graphs generated by Stats
    (r'^graph/apple/summary-total.png', 'graph_apple_summary_totals'),
    (r'^graph/apple/summary-feeds.png', 'graph_apple_summary_feeds'),
    (r'^graph/apple/feed_by_week/(?P<feed>.+).png', 'graph_apple_feed_weeks'),


    # Default page (aka, Stats home)
    (r'^$', 'index'),
)
