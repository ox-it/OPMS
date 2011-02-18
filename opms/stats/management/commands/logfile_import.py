# Import script for Apache Logfiles from media servers
# Author: Carl Marshall
# Last Edited: 4-2-2011

from django.core.management.base import BaseCommand, CommandError
from opms.stats.models import *
from opms.stats.uasparser import UASparser
import apachelog, datetime, sys, pygeoip
from dns import resolver,reversename
from IPy import IP
        
class Command(BaseCommand):
    args = '<spreadsheet.xls>'
    help = 'Imports the contents of the specified spreadsheet into the database'
    
    def __init__(self):
        self.geoip = pygeoip.GeoIP('/home/carl/Projects/opms_master/OPMS/data/geoip/GeoIP.dat',pygeoip.MMAP_CACHE)
        self.uasp = UASparser(cache_dir="/home/carl/Projects/opms_master/OPMS/opms/stats/ua_data/")

    def handle(self, *args, **options):

        for filename in args:
            # Some basic checking
            if filename.endswith('.gz'):
               raise CommandError("This file is still compressed. Uncompress and try again.\n\n")
               # sys.exit(1)
            else:
               print "################  Beginning IMPORT from", filename
        
            # Assume mpoau logfiles
            format = r'%Y-%m-%dT%H:%M:%S%z %v %A:%p %h %l %u \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
            p = apachelog.parser(format)
            
            log = open(filename)
            # This only needs setting/getting the once per call of this function
            logfile = self._logfile(filename)

            for line in log:
                data = p.parse(line)
                
# data.items()    
#[('%Y-%m-%dT%H:%M:%S%z', '2009-01-14T06:20:59+0000'),
# ('%l', '-'),
# ('%>s', '200'),
# ('%h', '163.1.2.86'),
# ('%A:%p', '163.1.3.25:80'),
# ('%{User-Agent}i', 'check_http/1.96 (nagios-plugins 1.4.5)'),
# ('%b', '207'),
# ('%{Referer}i', '-'),
# ('%u', '-'),
# ('%v', 'media.podcasts.ox.ac.uk'),
# ('%r', 'GET / HTTP/1.0')]
 
 
# data.get('%{User-Agent}i')
# 'check_http/1.96 (nagios-plugins 1.4.5)'
                
                # Validate the data - Count the number of elements
                if len(data) <> 11:
                    print "#### Houston, we have a problem with this entry: %s" % data
                
                
                # Status code validation
                status_code = 0
                for item in LogEntry.STATUS_CODE_CHOICES:
                    if int(data.get('%>s')) == item[0]:
                        status_code = int(data.get('%>s'))
                if status_code == 0:
                    print "#### Houston, we have a STATUS CODE 0 problem with this entry: %s" % data
                
                # Get or create the foreign key elements, Logfile, Rdns, FileRequest, Referer, UserAgent
                remote_rdns = self._ip_to_domainname(data.get('%h'))
                file_request = self._file_request(data.get('%r'))
                referer = self._referer(data.get('%{Referer}i'), status_code)
                user_agent = self._user_agent(data.get('%{User-Agent}i'))
                
                # Tracking needs dealing with later...
                
                # Pull apart the date time string
                date_string, time_string = data.get('%Y-%m-%dT%H:%M:%S%z').split('T')
                date_yyyy, date_mm, date_dd = date_string.split('-')
                time_hh, time_mm, time_ss = time_string.split(':')
                
                # Pull apart the server and port
                server_ip, server_port = data.get('%A:%p').split(':')
                
                # Size of response validation. Can be '-' when status not 200
                size_of_response = data.get('%b')
                if size_of_response.isdigit():
                    size_of_response = int(size_of_response)
                else:
                    size_of_response = 0
                
                # Build the log entry dictionary
                log_entry = {
                    'logfile': logfile,
                    'time_of_request': datetime.datetime(
                        int(date_yyyy), 
                        int(date_mm), 
                        int(date_dd), 
                        int(time_hh), 
                        int(time_mm), 
                        int(time_ss[0:2]) # Cut off the +0000
                        ),
                    'server_name': data.get('%v'),
                    'server_ip': IP(server_ip).strNormal(0),
                    'server_port': int(server_port),
                    'remote_ip': remote_rdns.ip_address,
                    'remote_logname': data.get('%l'),
                    'remote_user': data.get('%u'),
                    'remote_rdns': remote_rdns,
                    'status_code': status_code,
                    'size_of_response': size_of_response,
                    'file_request': file_request,
                    'referer': referer,
                    'user_agent': user_agent,
                }
                
                print '============================\n'
                print 'Data: %s\n' % data
                print 'log_entry=%s\n' % log_entry
                
                # Create if there isn't already a duplicate record in place
                obj, created = LogEntry.objects.get_or_create(
                    time_of_request = log_entry.get('time_of_request'),
                    server_ip = log_entry.get('server_ip'),
                    remote_ip = log_entry.get('remote_ip'),
                    size_of_response = log_entry.get('size_of_response'),
                    file_request = log_entry.get('file_request'),
                    defaults = log_entry)

                if created:
                    obj.save()
                    print '#### Record imported \n', obj
                else:
                    print "DUPLICATE RECORD DETECTED: %s\n" % log_entry

                print '============================\n'
                # TRACKING information needs to be parsed and stored now.
            
            # Bonus code here to split the arguments into tracking elements
            # tracking_list = fs[1].split('&')
            # for key_value in tracking_list:
            #    print "Key-Value = %s" % key_value
            # STORE THIS DATA EVENTUALLY!


            print "Import finished\n\n"


    def _logfile(self, filename):
        "Get or create a LogFile record for the given filename"
        
        # Simple hack for this method initially...
        logfile = {}
        logfile['service_name'] = "mpoau"
        logfile['file_name'] = "testname.log"
        logfile['file_path'] = "/testpath/"
        logfile['last_updated'] = datetime.datetime.utcnow()
        
        obj, created = LogFile.objects.get_or_create(
            service_name = logfile.get('service_name'),
            file_name = logfile.get('file_name'),
            file_path = logfile.get('file_path'),
            defaults = logfile)
        
        # If this isn't the first time, and the datetime is significantly different from last access, update the time
        if not created and (logfile.get('last_updated') - obj.last_updated).days > 0:
            obj.last_updated = logfile.get('last_updated')
        
        obj.save()

        return obj



    def _ip_to_domainname(self, ipaddress):
        "Returns the domain name for a given IP where known"
        # validate IP address
        # try: 
        adr = IP(ipaddress)
        # else:
        # PUT ERROR HANDLING IN HERE!
        
        rdns = {}
        rdns['ip_address'] = adr.strNormal(0)
        rdns['ip_int'] = adr.strDec(0)
        rdns['resolved_name'] = 'No Resolved Name'
        rdns['last_updated'] = datetime.datetime.utcnow()
        
        # Now get or create an Rdns record for this IP address
        obj, created = Rdns.objects.get_or_create(ip_address=rdns.get('ip_address'), defaults=rdns)
        
        if created:
            # Attempt an RDNS lookup, and remember to save this back to the object
            addr=reversename.from_address(rdns['ip_address'])
            try:
                obj.resolved_name = str(resolver.query(addr,"PTR")[0])
            except NXDOMAIN:
                print 'NXDOMAIN error trying to resolve:',addr
            
            # Go get the location for this address
            obj.country_code = self.geoip.country_code_by_addr(rdns.get('ip_address'))
            obj.country_name = self.geoip.country_name_by_addr(rdns.get('ip_address'))
            
            obj.save()

        return obj



    def _file_request(self, request_string):
        "Get or create a FileRequest object for a given request string"
        
        # Example request strings
        # GET /philfac/lockelectures/locke_album_cover.jpg HTTP/1.1
        # GET / HTTP/1.0
        # GET /oucs/oxonian_interviews/300by300_interview.png HTTP/1.0
        # GET /robots.txt HTTP/1.0
        # GET /astro/introduction/astronomy_intro-medium-audio.mp3?CAMEFROM=podcastsGET HTTP/1.1
        
        # Crude splitting... first on spaces, then on file/querystring
        ts = request_string.split()
        fs = ts[1].split('?')
        
        fr = {}
        fr['method'] = ts[0]
        fr['uri_string'] = fs[0]
        fr['protocol'] = ts[2]
        
        # Querystring is optional, so test for it first.
        if len(fs)==2:
            fr['argument_string'] = fs[1]
        else:
            fr['argument_string'] = ""
        
        # Crude file typing (in lieu of an actual file database...)
        # Take the last three letters of the filename and compare to known types
        ft = fr.get('uri_string')[-3:].lower()
        fr['file_type'] = ""
        for item in FileRequest.FILE_TYPE_CHOICES:
            if ft == item[0]:
                fr['file_type'] = ft
        
        # Now get or create a FileRequest record for this string
        obj, created = FileRequest.objects.get_or_create(
            method = fr.get('method'), 
            uri_string = fr.get('uri_string'),
            argument_string = fr.get('argument_string'),
            protocol = fr.get('protocol'),
            defaults = fr)
        
        if created:
            obj.save()
        
        return obj



    def _referer(self, referer_string, status_code):
        "Get or create a Referer record for the given string"
        ref = {}
        ref['full_string'] = ""
        
        if status_code in (200,206,304):
            ref['full_string'] = referer_string
        
        # Now get or create a Referer record for this string
        obj, created = Referer.objects.get_or_create(
            full_string = ref.get('full_string'),
            defaults = ref)
        
        if created:
            obj.save()
        
        return obj



    def _user_agent(self, agent_string):
        "Get or create a UserAgent record for the given string"
        user_agent = {}
        
        # Store the full string for later analysis
        user_agent['full_string'] = agent_string
        
        # Create some defaults that we'll likely overwrite. OS and UA can be null, so ignore.
        user_agent['type'] = ""
        
        # Now get or create a UserAgent record for this string
        obj, created = UserAgent.objects.get_or_create(
            full_string = user_agent.get('full_string'), 
            defaults = user_agent)
        
        if created:
            # Parse the string to extract the easy bits
            uas_dict = self.uasp.parse(user_agent.get('full_string'))

            #Set the type string
            obj.type = uas_dict.get('typ')
            
            # Deal with the OS record
            os = {}
            os['company'] = uas_dict.get('os_company')
            os['family'] = uas_dict.get('os_family')
            os['name'] = uas_dict.get('os_name')
            
            # Now get or create an OS record
            obj.os, created = OS.objects.get_or_create(
                company = os.get('company'), 
                family = os.get('family'), 
                name = os.get('name'), 
                defaults = os)
            if created:
                obj.os.save()
                
            
            # Deal with the UA record
            ua = {}
            ua['company'] = uas_dict.get('ua_company')
            ua['family'] = uas_dict.get('ua_family')
            ua['name'] = uas_dict.get('ua_name')
            
            # Now get or create an UA record
            obj.ua, created = UA.objects.get_or_create(
                company = ua.get('company'), 
                family = ua.get('family'), 
                name = ua.get('name'), 
                defaults = ua)
            if created:
                obj.ua.save()
        
            # Finally store the new and updated UserAgent object
            obj.save()
        
        return obj
