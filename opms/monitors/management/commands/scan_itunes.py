# Perform various scans of URLs from iTunes Store
# Author: Carl Marshall
# Last Edited: 08-12-2011
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from monitors.utils import itunes as itunes
from monitors.models import ItuCollectionChartScan, ItuCollectionHistorical, ItuCollection, ItuItemChartScan, ItuItemHistorical, ItuItem, ItuScanLog, ItuGenre, ItuInstitution
import datetime, sys
from dateutil.parser import *
import urllib2

class Command(BaseCommand):
    help = 'Scan iTunes U Service (1:Institutional collection <default>; 2:Top Collections; 3:Top Downloads)'
    args = "<institution>"
    label = "institution"
    option_list = BaseCommand.option_list + (
        make_option('--mode', action='store', dest='mode',
            default=1, help='Specify the type of scan to be done (1,2,3)'),
    )

    def __init__(self):
        # Toggle debug statements on/off
        self.debug = False
        # Error logging file and string cache
        self.error_log = ""
        self.error_cache = ""

        super(Command, self).__init__()

    def handle(self, institution = "Oxford University",**options):
        # Some basic error checking
        if institution is None:
            raise CommandError("Please specify the institution to scan.")
        try:
            url = itunes.INSTITUTIONAL_URLS[institution]
        except:
            raise CommandError(institution + "is not a recognised institution. Recognised institutions are:\n" + "\n".join(itunes.INSTITUTIONAL_URLS.keys()))

        try:
            mode = int(options.get("mode",1))
        except ValueError:
            raise CommandError("""Please specify a valid mode for this scan.
               1) Scan an institution's collection
               2) Scan the Top Collections chart
               3) Scan the Top Downloads chart
               """)
        if mode < 1 or mode > 3:
            raise CommandError("""Please specify a valid mode for this scan.
               1) Scan an institution's collection
               2) Scan the Top Collections chart
               3) Scan the Top Downloads chart
               """)

        scantime = datetime.datetime.now()
        print "Scan iTunes started at " + str(datetime.datetime.utcnow()) + "\n"
        # Create an error log
        self._errorlog_start('scan_itunes.log')

        scanlog = ItuScanLog(starting_url=url, mode=mode, time=scantime, comments="")
        scanlog.save()

        if mode == 1:
            comment = "Scan (and update) of " + institution + "\'s collection from %s" % url
            self._errorlog("Log started for: %s" % comment)
            print comment

            print("Getting information about collections...")
            collections = itunes.get_institution_collections(url)
            print("Processing collection information and scanning individual items...")
            collections_spotted = []
            items_spotted = []
            for c in collections:
                if c:
#                    for k in c.keys():
#                        print(k + ': ' + c[k])

                    #Check if this collection's institution exists - if not, create it.
                    i = ItuInstitution(name=c['institution'], itu_id=int(c['institution_id']), url=c['institution_url'])
                    i_exists = False
                    for saved_i in ItuInstitution.objects.all():
                        if int(i.itu_id) == int(saved_i.itu_id) and i.name==saved_i.name and i.url==saved_i.url:
                            i_exists = True
                            i = saved_i
                    if i_exists==False:
                        print('Creating new institution ' + i.name)
                        i.save()

                    #Check if this collection's genre exists - if not, create it.
                    g = ItuGenre(name=c['genre'], itu_id=int(c['genre_id']), url=c['genre_url'])
                    g_exists = False
                    for saved_g in ItuGenre.objects.all():
                        if int(g.itu_id) == int(saved_g.itu_id) and g.name==saved_g.name and g.url==saved_g.url:
                            g_exists = True
                            g = saved_g
                    if g_exists==False:
                        print('Creating new genre ' + g.name)
                        g.save()

                    cr = ItuCollection(institution=i)
                    cp = ItuCollectionHistorical(name=c['series'],
                                                 itu_id=int(c['series_id']),
                                                 img170=c['series_img_170'],
                                                 url=c['series_url'],
                                                 language=c['language'],
                                                 last_modified=parse(c['last modified']).date(),
                                                 contains_movies=c['contains_movies'],
                                                 missing=None,
                                                 version=1,
                                                 institution=i,
                                                 scanlog=scanlog,
                                                 genre=g,
                                                 previous=None,
                                                 itucollection=cr)

                    #Put together a list of saved cps that look like they're the same as our cp, really.
                    similar_cps = []
                    cp_exists = False
                    for saved_cp in ItuCollectionHistorical.objects.all():
                        if (cp.name==saved_cp.name and cp.contains_movies==saved_cp.contains_movies) or cp.itu_id==saved_cp.itu_id or cp.url==saved_cp.url: #name AND Video/Audio
                            if cp.url != saved_cp.url: #Don't add similar cp if the URLs are different, but both are accessible.
                                try:
                                    urllib2.urlopen(cp.url)
                                    urllib2.urlopen(saved_cp.url)
                                except urllib2.URLError:
                                    similar_cps.append(saved_cp)
                            else:
                                similar_cps.append(saved_cp)
                        if cp.name==saved_cp.name and cp.contains_movies==saved_cp.contains_movies and int(cp.itu_id)==int(saved_cp.itu_id) and cp.url==saved_cp.url and cp.img170==saved_cp.img170 and cp.language==saved_cp.language:
                            cp_exists=True
                            cp = saved_cp
                    if cp_exists==False:
                        if similar_cps:
                            similar_cps.sort(key=lambda this_cp: this_cp.version)
                            latest_similar_cp = similar_cps[-1]
                            cp.previous = latest_similar_cp
                            cp.version = latest_similar_cp.version + 1
                            cp.itucollection = latest_similar_cp.itucollection
                        else:
                            cr.save()
                            cp.itucollection = cr
                        print('Creating new periodic collection record for ' + cp.name + ', version ' + str(cp.version))
                        cp.save()

                    collections_spotted.append(cp)

                    #Acquire the list of items for this collection.
                    items = itunes.get_collection_items(cp.url)
                    for item in items:
                        if item:
                            itemr = ItuItem(institution=i)
                            #Deal with things with no duration (like PDFs...)
                            if 'duration' in item.keys():
                                item['duration'] = int(item['duration'])
                            else:
                                item['duration'] = None
                            itemp = ItuItemHistorical(name=item['songName'],
                                                    itu_id=item['itemId'],
                                                    url=item['url'],
                                                    artist_name=item['artistName'],
                                                    description=item['description'],
                                                    duration=item['duration'],
                                                    explicit=bool(item['explicit']),
                                                    feed_url=item['feedURL'],
                                                    file_extension=item['fileExtension'],
                                                    kind=item['kind'],
                                                    long_description=item['longDescription'],
                                                    playlist_id=int(item['playlistId']),
                                                    playlist_name=item['playlistName'],
                                                    popularity=float(item['popularity']),
                                                    preview_length=int(item['previewLength']),
                                                    preview_url=item['previewURL'],
                                                    rank=int(item['rank']),
                                                    release_date=parse(item['releaseDate'],ignoretz=True),
                                                    missing=None,
                                                    version=1,
                                                    previous=None,
                                                    ituitem=itemr,
                                                    institution=i,
                                                    genre=g,
                                                    scanlog=scanlog,
                                                    series=cp,
                                                    )
                            #Put together a list of saved itemps that look like they're the same as our itemp, really.
                            similar_itemps = []
                            itemp_exists = False
                            for saved_itemp in ItuItemHistorical.objects.filter(series=cp):
                                if (itemp.name==saved_itemp.name or itemp.itu_id==saved_itemp.itu_id or itemp.url==saved_itemp.url) and itemp.file_extension==saved_itemp.file_extension: #name AND Video/Audio
                                    if itemp.url != saved_itemp.url: #Don't add similar itemp if the URLs are different, but both are accessible.
                                        try:
                                            urllib2.urlopen(itemp.url)
                                            urllib2.urlopen(saved_itemp.url)
                                        except urllib2.URLError:
                                            similar_itemps.append(saved_itemp)
                                    else:
                                        similar_itemps.append(saved_itemp)
                                if itemp.name==saved_itemp.name and itemp.itu_id==saved_itemp.itu_id and itemp.url==saved_itemp.url and itemp.artist_name==saved_itemp.artist_name and itemp.description==saved_itemp.description and itemp.duration==saved_itemp.duration and itemp.explicit==saved_itemp.explicit and itemp.feed_url==saved_itemp.feed_url and itemp.file_extension==saved_itemp.file_extension and itemp.kind==saved_itemp.kind and itemp.long_description==saved_itemp.long_description and itemp.playlist_id==saved_itemp.playlist_id and itemp.playlist_name==saved_itemp.playlist_name and itemp.popularity==saved_itemp.popularity and itemp.preview_length==saved_itemp.preview_length and itemp.preview_url==saved_itemp.preview_url and itemp.rank==saved_itemp.rank and itemp.release_date==saved_itemp.release_date:
                                    itemp_exists=True
                                    itemp = saved_itemp
                            if itemp_exists==False:
                                if similar_itemps:
                                    similar_itemps.sort(key=lambda this_itemp: this_itemp.version)
                                    latest_similar_itemp = similar_itemps[-1]
                                    itemp.previous = latest_similar_itemp
                                    itemp.version = latest_similar_itemp.version + 1
                                    itemp.ituitem = latest_similar_itemp.ituitem
                                else:
                                    itemr.save()
                                    itemp.ituitem = itemr
                                print('Creating new periodic item record for ' + itemp.name + ', version ' + str(itemp.version))
                                itemp.save()
                            items_spotted.append(itemp)
                        else:
                            print('WARNING: Blank item - perhaps we couldn\'t download the appropriate page?')
                else:
                    print('WARNING: Blank category - perhaps we couldn\'t download the appropriate page?') #TODO: Find the mystery bug that causes pages to fail to download.
            print("Checking whether anything has gone missing or reappeared...")
            institution = ItuInstitution.objects.filter(name=collections[0]['institution'])[0]
            for h in ItuCollectionHistorical.objects.all():
                if h.institution == institution:
                    if h == h.latest():
                        if h not in collections_spotted and h.missing == None:
                            print(h.name + " appears to have gone missing! We last saw it at " + str(h.scanlog.time))
                            h.missing = scanlog
                            h.save()
                        elif h in collections_spotted and h.missing:
                            print(h.name + " has reappeared! It went missing at" + str(h.missing.time))
                            h.missing = None
                            h.save()
            for h in ItuItemHistorical.objects.all():
                if h.institution == institution:
                    if h == h.latest():
                        if h not in items_spotted and h.missing == None:
                            print(h.name + " appears to have gone missing! We last saw it at " + str(h.scanlog.time))
                            h.missing = scanlog
                            h.save()
                        elif h in items_spotted and h.missing:
                            print(h.name + " has reappeared! It went missing at" + str(h.missing.time))
                            h.missing = None
                            h.save()
        elif mode == 2:
            comment = "Scan of an Top Collections Chart from %s" % url
            self._errorlog("Log started for: %s" % comment)
            print comment
            collections = itunes.get_topcollections()
            for c in collections:
                if c:
                    historical_collections=ItuCollectionHistorical.objects.filter(url=c['series_url'])
                    if historical_collections:
                        historical_collection=historical_collections[0].latest()
                        print('Creating new chart row: ' + historical_collection.name + ' Position: ' + str(c['chart_position']))
                        chartrow=ItuCollectionChartScan(position=int(c['chart_position']),itucollection=historical_collection.itucollection,itucollectionperiodic=historical_collection,scanlog=scanlog,date=scanlog.time)
                        chartrow.save()
                    else:
                        print('WARNING: Couldn\'t find an historical record of collection at ' + c['series_url'] + '. Perhaps do an historical scan of ' + c['institution'] + ' first?')

        elif mode == 3:
            comment = "Scan of an Top Downloads Chart from %s" % url
            self._errorlog("Log started for: %s" % comment)
            print comment
            items = itunes.get_topdownloads()
            for i in items:
                if i:
                    historical_items=ItuItemHistorical.objects.filter(name=i['item'])
                    if historical_items:
                        historical_item=historical_items[0].latest()
                        print('Creating new download chart row: ' + historical_item.name + ' Position: ' + str(i['chart_position']))
                        chartrow=ItuItemChartScan(position=int(i['chart_position']),ituitem=historical_item.ituitem,ituitemperiodic=historical_item,scanlog=scanlog,date=scanlog.time)
                        chartrow.save()
                    else:
                        print('WARNING: Couldn\'t find an historical record of item at ' + i['item_url'] + '. Perhaps do an historical scan of ' + i['institution'] + ' first?')

        else:
            comment = "We shouldn't ever get this scan..."
            print comment


        print "\nScan iTunes finished at " + str(datetime.datetime.utcnow())

        # Write the error cache to disk
        self._error_log_save()
        self._errorlog_stop()
        scanlog.complete = True
        scanlog.save()
        return None

    def _get_or_create_genre(self, id):
        return None

    def _get_or_create_institution(self, id):
        return None

    def _get_or_create_series(self, series):
#        series_dict = {}
#        series_dict['name'] =
#        series_dict['itu_id'] =
#        series_dict['img170'] =
#        series_dict['img75'] =
#        series_dict['url'] =
#        series_dict['language'] =
#        series_dict['last_modified'] =
#        series_dict['genre'] =
#        series_dict['institution'] =
        return None, False


    # DEBUG AND INTERNAL HELP METHODS ==============================================================

    def _debug(self,error_str):
        "Basic optional debug function. Print the string if enabled"
        if self.debug:
            print 'DEBUG:' + str(error_str) + '\n'
        return None


    def _errorlog(self,error_str):
        "Write errors to a log file"
        # sys.stderr.write('ERROR:' + str(error_str) + '\n')
        #self.error_log.write('ERROR:' + str(error_str) + '\n')
        self.error_cache += 'ERROR:' + str(error_str) + '\n'
        return None


    def _errorlog_start(self, path_to_file):
        try:
            self.error_log = open(path_to_file,'a')
        except IOError:
            sys.stderr.write("WARNING: Could not open existing error file. New file being created")
            self.error_log = open(path_to_file,'w')

        self.error_log.write("Log started at " + str(datetime.datetime.utcnow()) + "\n")
        print "Writing errors to: " + path_to_file
        return None

    def _error_log_save(self):
        "Write errors to a log file"
        self.error_log.write(self.error_cache)
        self.error_cache = ""
        return None


    def _errorlog_stop(self):
        self.error_log.write("Log ended at " + str(datetime.datetime.utcnow()) + "\n")
        self.error_log.close()
        return None