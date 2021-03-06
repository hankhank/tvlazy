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
        self.logger = logging.getLogger('tvlazy')
        self.location = location
        self.series = series
        self.ep = ep
        self.season = season
        self.quality = quality

    def epFromRawString(self, rawstr):
        self.logger.info("Not yet implemented")

    def moveEp(self, location):
        self.logger.info("Moving to %s" % location)

    def renameEp(self, newname):
        self.logger.info("Not yet implemented")

    def delEp(self):
        self.logger.info("Not yet implemented")

    def epNumber(self):
        return self.ep

    def __eq__(self, other):
        return (self.ep == other.ep and self.season == other.season)

    def __ne__(self, other):
        return (self.ep != other.ep or self.season != other.season)

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
        # get folder and try and extract video
        self.extractRars(self.tordir)
        # get video files
        vids = self.findVids(self.tordir)   
        # remove samples
        vids = self.removeSamples(vids)
        if( vids ):
            for v in vids:
               shutil.move(os.path.join(self.tordir, v),location)

    def extractRars(self, tordir):
        for fs in self.files: # group rars
            try: filetype = runBash('file {}/{}'.format(
                self.download_dir,fs)).split(' ', 1)[1]
            except: continue
            if filetype.startswith('RAR archive'):
            # get name of files to be extracted
                cmd = ('unrar x -y %s %s'% (os.path.join(self.download_dir, fs),
                    tordir))
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
        if( tvep.season and tvep.ep and not tvep in eps):
            print "we need to add %s %s %s" %  (tvep.series,tvep.season,tvep.ep)
            seasons = self.seasons.keys()
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
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out = p.stdout.read().strip()
    os.waitpid(p.pid,0)
    return out

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
        remove = True;
        # Checktime
        now = datetime.datetime.now()
        remove &= ((now - torr.date_done) > datetime.timedelta(days=int(daysold)))
        # Check ratio
        if( ratio < 0 ):
            remove &= (int(torr.ratio) < abs(ratio))
        else:
            remove &= (int(torr.ratio) > ratio)
        if(remove):
            print 'Removing Torrent %s ratio %s date %s' % (torr.name, torr.ratio, torr.date_done)
            torrentclient.remove(torrid, delete_data=True)

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
                help='Ratio after which to delete torrents if positive. \
                    If negative ratio before to delete torrents',
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
    # Maintain New-list
    opt.add_option('--new_list', '-n',
                action = 'store',
                help='Maintain a newlist of the newest 50 videos in \
                    at this location chronological order',
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

    # Connect to client and create the collection
    tc = transmissionrpc.Client(address=options.clientip, port=options.clientport)
    torrentlist = tc.list()
    tvcol = TvCollection("/home/andrew/TvShows/")
    
    # New movies/tveps list
    newtv = []
    newmovie = []

    if( options.tv_sort != '' ):
        # find tv series
        series = tvcol.getSeries()
        for tor in torrentlist:
            torrent = tc.info(tor)[tor]
            if( int(torrent.progress) == int(100) ): 
                # See if it matches our collection
                for s in series:
                    t = SeriesParser(s)
                    try: 
                        t.parse(torrent.name) 
                    except: 
                        logger.error("Tried to parse but failed %s" % torrent.name)
                    if( t.valid ):
                        ep = TorrentTvEpisode(t.name, t.episode, t.season, t.quality, torrent.files())
                        tvcol.addEpisode(ep)
                        newtv.append(ep)
        return

    if( options.cleanup ):
        cleanupOldTorrents(tc, int(options.ratio), options.old);
        return
    
    newtv.append(ep)
    MAX_NEW_LIST = 10
    logger.error('newtv {} newlist {}'.format(newtv, newlist))
    if( options.new_list != '' ):
        # Get current new list
        newlinks = os.listdir(options.new_list)
        newlinks = [(os.lstat(os.path.join(options.new_list, n)).st_ctime,
            n) for n in newlinks]
        newlinks.sort() # Ascending
        if(len(newtv) > 0):
            # Remove old 
            dellinks = []
            if((len(newlinks)+len(newtv)) > MAX_NEW_LIST):
                dellinks = newlinks[(len(newlinks)+len(newtv)) - MAX_NEW_LIST:]
                logger.erro('old links {}'.format(dellinks))
                for d in delinks:
                    print d
                    os.remove(os.path.join(options.new_list, d))
            # Add new
            for ep in newtv:
                src = "%s" % ep.location
                dst = "%s/%s-s%02d%02d" % (options.new_list, ep.series,
                    int(ep.season), int(ep.ep))
                os.symlink(src, dst)
                logger.error( '{}->{}'.format(src, dst))

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
        
def main():
    controller()

if __name__ == '__main__':
    main()
