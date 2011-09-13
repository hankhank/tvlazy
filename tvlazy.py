#! /usr/bin/python
import subprocess
import optparse
import re
import os
import transmissionrpc
import titles
import datetime

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
        torr = tc.info(torrid)[torrid]
        # Old torrent removal
        remove = False;
        # Checktime
        now = datetime.datetime.now()
        remove |= ((now - torr.date_done) > datetime.timedelta(days=int(options.old)))
        # Check status
        remove |= (torr.status == 'stopped')
        # Check ratio
        remove |= (torr.ratio > options.ratio)
        if(remove and TEST):
            print 'TEST: Removing Torrent %s' % (torr.name)
        elif(remove):
            tc.remove(torrid, delete_data=True)

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
    opt.add_option('--tv-sort', '-t',
                action = 'store',
                help='Sort tv eps to this location',
                default='')
    opt.add_option('--movie-sort', '-m',
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

    # Connect to client
    tc = transmissionrpc.Client(address=options.clientip, port=options.clientport)
    
    if( options.cleanup ):
        cleanupOldTorrents(tc, options.ratio, options.old);
    if( options.tv-sort || options.movie-sort ):
        # Get environment variables
        torr_id = os.environ['TR_TORRENT_ID']
        torr_dir = os.environ['TR_TORRENT_DIR']
        torr_name = os.environ['TR_TORRENT_NAME']

        
    def main():
    controller()

if __name__ == '__main__':
    main()
