#! /usr/bin/python
import subprocess
import optparse
import re
import os
import transmissionrpc
import titles
import datetime
import logging
import shutil
from titles import SeriesParser

class TvEpisode ():
    def __init__(self, location, series, ep, season, quality):
        self.location = location
        self.series = series
        self.ep = ep
        self.season = season
        self.quality = quality

    def epFromRawString(self, rawstr):
        print "Not yet implemented"
    def moveEp(self, location):
        print "MOVING to %s" % location
    def renameEp(self, newname):
        print "Not yet implemented"
    def delEp(self):
        print "Not yet implemented"
    def epNumber(self):
        return self.ep
    def __eq__(self, other):
        return (self.ep == other.ep and self.season == other.season)
           # and self.quality == other.quality)
    def __ne__(self, other):
        return (self.ep != other.ep or self.season != other.season 
            or self.quality == other.quality)

class TorrentTvEpisode (TvEpisode):

    vids_regex = '.(mkv|avi)' # needs to ignore caseseason_num
    sample_regex = 'sample' # needs to ignore caseseason_num
    rar_regex = '((.*)\.rar)|((.*)\.r00)'

    def __init__(self, series, ep, season, quality, files):
        TvEpisode.__init__(self, '', series, ep, season, quality)
        self.files = [ f['name'] for f in files.values()]
        self.download_dir = "/home/andrew/Downloads"
        self.tordir = os.path.join(self.download_dir, os.path.dirname(self.files[0]).split('/',1)[0])

    def moveEp(self, location):
        print "Torrent MOVING to %s" % location
        # get folder and try and extract video
        self.extractRars(self.tordir)
        # get video files
        vids = self.findVids(self.tordir)   
        print vids
        # remove samples
        vids = self.removeSamples(vids)
        print vids
        if( vids ):
            for v in vids:
               shutil.move(os.path.join(self.tordir, v),location)

    def extractRars(self, tordir):
        rar_re = re.compile(self.rar_regex, re.IGNORECASE)
        for f in self.files:
            if( rar_re.match(f) ):
                # get name of files to be extracted
                cmd = ('unrar x -y %s %s'% (os.path.join(self.download_dir, f), tordir))
                runBash(cmd)
                return

    def removeSamples(self, files):
        ret_vids = []
        samp_re = re.compile(self.sample_regex, re.IGNORECASE)
        for f in files:
            if( not samp_re.search(f) ):
                ret_vids.append(f)
        return ret_vids

    def findVids(self, tordir):
        ret_vids = []
        vids_re = re.compile(self.vids_regex, re.IGNORECASE)
        files = os.listdir(tordir)
        for f in files:
            split_file = os.path.splitext(os.path.basename(f))
            if( len(split_file) == 2):
                if( vids_re.match(split_file[1]) ):
                    ret_vids.append(f)
        return ret_vids
    

# Represents current tv series stored on disk.
# Allows easy addition/subtraction of eps etc..
class TvSeries ():
    
    season_regex = '.*season[\s]*([0-9]*).*' # needs to ignore caseseason_num

    def __init__(self, directory):
        self.logger = logging.getLogger('tvlazy')
        if( not directory ):
            self.logger.error('Should have been given directory')
            return
        # Collect the series name
        self.seriesname = os.path.basename(directory)
        # Collect seasons
        self.seasons = {} # Create empty seasons container
        self.directory = directory
        subdir = os.listdir(self.directory)
        season_re = re.compile(self.season_regex, re.IGNORECASE)
        for season in subdir:
            if os.path.isdir(os.path.join(self.directory, season)):
                self.logger.debug('Found a season %s' % season)
                season_mat = season_re.match(season)
                if( season_mat ):
                    self.logger.debug('Season number %s' % season_mat.group(1))
                    season_num = str(season_mat.group(1))
                    season_path = os.path.join(self.directory, season)
                    self.seasons[season_num] = { 'directory': season_path,
                                                'text': season,
                                                'episodes': {} }
                    # Collect Episodes
                    season_eps = os.listdir(season_path)
                    t = SeriesParser(self.seriesname, identified_by='ep')
                    for ep in season_eps:
                        ep_path = os.path.join(season_path, ep)
                        try: 
                            t.parse(ep)
                        except: 
                            print ep
                        if( t.valid ):
                            new_ep = TvEpisode(ep_path, t.name, t.episode, t.season, t.quality)
                            self.seasons[season_num]['episodes'][new_ep.epNumber()] = new_ep

    def addEpisode(self, tvep):
        eps = self.listEpisodes()
        if( not tvep in eps):
            print "we need to add %s %s %s" %  (tvep.series,tvep.season,tvep.ep)
            seasons = self.seasons.keys()
            print seasons
            if( not str(tvep.season) in seasons):
                self.addSeason(tvep.season)   
            tvep.moveEp(self.seasons[str(tvep.season)]['directory'])
        return       
    def delEpisode(self, tvep):
        print "Not yet implemented"
    # Season 0 is all seasons
    def listEpisodes(self, season = 0):
        if( season == 0 ):
            return [ ep for s in self.seasons.values() for ep in s['episodes'].values()]
        else:
            return [ ep for ep in self.seasons[season]['episodes'].values()]

    def listSeasons(self):
        print "Not yet implemented"
    def delSeason(self):
        print "Not yet implemented"
    def addSeason(self, newseason):
        season_path = os.path.join(self.directory, "Season %s" % newseason)
        os.makedirs(season_path)
        self.seasons[newseason] = { 'directory': season_path,
                                        'text': newseason,
                                        'episodes': {} }
    def getSeriesName(self):
        return self.seriesname
    def printSeries(self):
        print self.seriesname
        for s in self.seasons.keys():
            print "\tSeason %s" % s
            for e in self.seasons[s]['episodes']:
                print"\t\tEpisode %s" % e

class TvCollection():
    def __init__(self, location):
        self.directory = location
        subdir = os.listdir(self.directory)
        self.tvcol= {}
        for series in subdir:
            series_path = os.path.join(self.directory, series)
            new_series = TvSeries(series_path)
            self.tvcol[new_series.getSeriesName()] = new_series
    def printAll(self):
        for new_series in  self.tvcol.values():
            new_series.printSeries()
    def getSeries(self):
        return self.tvcol.keys()
    def addEpisode(self, tvep):
        # Assume we have the series for now
        series = self.tvcol[tvep.series]
        series.addEpisode(tvep)
            

def runBash(cmd):
    p = subprocess.Popen(cmd, shell=True)
    os.waitpid(p.pid,0)

def report(output,cmdtype="UNIX COMMAND:"):
     print output

def escapedir(dir):
    return dir.replace(" ","\ ")

# Cleans up torrents on torrent client that are over ratio 
# and older than specified.
def cleanupOldTorrents(torrentclient, ratio, daysold):
    torrentlist = torrentclient.list()
    for torrid in torrentlist:
        torr = torrentclient.info(torrid)[torrid]
        # Old torrent removal
        remove = False;
        # Checktime
        now = datetime.datetime.now()
        remove |= ((now - torr.date_done) > datetime.timedelta(days=int(daysold)))
        # Check status
        remove |= (torr.status == 'stopped')
        # Check ratio
        remove |= (torr.ratio > ratio)
        if(remove):
            print 'TEST: Removing Torrent %s' % (torr.name)
        #elif(remove):
         #   tc.remove(torrid, delete_data=True)

def controller():
    opt = optparse.OptionParser(description="does stuff for tv",
    								prog="tvlazy",
    								version="3.14",
    								usage="%prog directory ")
    opt.add_option('--clientip', '-c',
                action = 'store',
                help='Client ip address of transmission client',
                default='192.168.1.109')
    opt.add_option('--clientport', '-p',
                action = 'store',
                help='Client port of transmission client',
                default='9091')
# Clean-up options
    opt.add_option('--cleanup', '-C',
                action = 'store_true',
                help='Set this flag if you want to clean up old torrents',
                default=False)
    opt.add_option('--ratio', '-r',
                action = 'store',
                help='Ratio after which to delete torrents',
                default='3')
    opt.add_option('--old', '-o',
                action = 'store',
                help='Time in days after which to delete torrents',
                default=40)
# Sort torrent
    opt.add_option('--tv_sort', '-v',
                action = 'store',
                help='Sort tv eps to this location',
                default='')
    opt.add_option('--movie_sort', '-m',
                action = 'store',
                help='Sort movies to this location',
                default='')
    opt.add_option('--test', '-t',
                action = 'store_true',
                help='Test config etc.. no changes made',
                default=False)
	
    options, arguments = opt.parse_args()
    if len(arguments) < 0:
    	opt.print_help()
    	return
    TEST = options.test

    # Setting up logging
    logger = logging.getLogger('tvlazy')
    logger.setLevel(logging.INFO)
    #fh = logging.FileHandler('spam.log')
    #fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    #logger.addHandler(fh)
    logger.addHandler(ch)

    # Connect to client
    tc = transmissionrpc.Client(address=options.clientip, port=options.clientport)
    torrentlist = tc.list()
    tvcol = TvCollection("/home/andrew/TvShows/")
    if( options.cleanup ):
        # find tv series
        series = tvcol.getSeries()
        for tor in torrentlist:
            torrent = tc.info(tor)[tor]
            # See if it matches our collection
            for s in series:
                t = SeriesParser(s)
                try: 
                    t.parse(torrent.name) 
                except: 
                    print "ad"
                if( t.valid ):
                    ep = TorrentTvEpisode(t.name, t.episode, t.season, t.quality, torrent.files())
                    tvcol.addEpisode(ep)
        return
        cleanupOldTorrents(tc, options.ratio, options.old);
    if( options.tv_sort or options.movie_sort ):
        # Get environment variables
        try:
            torr_id = os.environ['TR_TORRENT_ID']
            torr_dir = os.environ['TR_TORRENT_DIR']
            torr_name = os.environ['TR_TORRENT_NAME']
        except KeyError:
            torr_id = 1
            logger.error("No torrent info")
        torr = tc.info(torr_id)[torr_id]
        # Do we need to extract any files?
        for f in torr.files():
            print f
        return
        b = TvCollection("/home/andrew/TvShows/")
        t = SeriesParser("Burn Notice")
        print t.parse("Burn.Notice.S05E09.720p.HDTV.X264-DIMENSION").name

        
def main():
    controller()

if __name__ == '__main__':
    main()
