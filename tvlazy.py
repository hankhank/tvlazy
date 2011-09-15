#! /usr/bin/python
import subprocess
import optparse
import re
import os
import transmissionrpc
import titles
import datetime
import logging
from titles import SeriesParser

class TvEpisode ():
    def __init__(self, location, rawname=''):
        self.ep_path = location
    def epFromRawString(self, rawstr):
        print "Not yet implemented"
    def moveEp(self, location):
        print "Not yet implemented"
    def renameEp(self, newname):
        print "Not yet implemented"
    def delEp(self):
        print "Not yet implemented"
    def epNumber(self):
        print "Not yet implemented"
        return '1'


# Represents current tv series stored on disk.
# Allows easy addition/subtraction of eps etc..
class TvSeries ():
    
    season_regex = 'season[\s]*([0-9]*)' # needs to ignore case

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
                    for ep in season_eps:
                        ep_path = os.path.join(season_path, ep)
                        new_ep = TvEpisode(ep_path)
                        self.seasons[season_num]['episodes'][new_ep.epNumber()] = new_ep

    def addEpisode(self, tvep):
        print "Not yet implemented"
    def delEpisode(self, tvep):
        print "Not yet implemented"
    # Season 0 is all seasons
    def listEpisodes(self, season = 0):
        print "Not yet implemented"
    def listSeasons(self):
        print "Not yet implemented"
    def delSeason(self):
        print "Not yet implemented"
    def addSeason(self):
        print "Not yet implemented"
    def getSeriesName(self):
        return self.seriesname

class TvCollection():
    def __init__(self, location):
        self.directory = location
        subdir = os.listdir(self.directory)
        self.tvcol= {}
        for series in subdir:
            series_path = os.path.join(self.directory, series)
            new_series = TvSeries(series_path)
            self.tvcol[new_series.getSeriesName()] = new_series
    def getSeries(self):
        return self.tvcol.keys()

def runBash(cmd):
    p = subprocess.Popen(cmd, shell=True)
    os.waitpid(p.pid,0)

def report(output,cmdtype="UNIX COMMAND:"):
     print output

def escapedir(dir):
    return dir.replace(" ","\ ")

# Extracts Series if needs be
def extractRars(location):
    logger = logging.getlogger('tvlazy')
    ls = os.walk(arguments[0])
    for i in ls:
    	rargroups = list()
    	rgroups = list()
    	for files in i[2]: # group rars
            rar = re.match('((.*)\.rar)|((.*)\.r00)', files)
            if rar:
                rar = rar.groups()
                rarext  = rar[0] # name and ext
                rarname = rar[1] # name no ext
                rext    = rar[2] # r# and ext
                rname   = rar[3] # r# no ext
                if rarname:
                    if not (rarname+".r00") in rargroups:
                        rargroups.append(rarext)
                elif rname:
                    if not (rname+".rar") in rargroups:
                        rargroups.append(rext)
        # process
        for g in rargroups:
            logger.info("unrarding %s" % g[:-4])
            cmd = ('unrar x %s %s'% (escapedir( i[0] +'/'+ g),escapedir(i[0])))
            runBash(cmd)


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
    logger.setLevel(logging.DEBUG)
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
            # Compare against all series
            for s in series:
                t = SeriesParser(s)
                try: 
                    pres = t.parse(torrent.name) 
                except: 
                    print "ad"
                if( pres ):
                    print pres.name
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
