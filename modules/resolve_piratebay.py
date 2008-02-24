import urllib
import urllib2
import urlparse
import logging

log = logging.getLogger("newtorrents")

# this way we don't force users to install bs incase they do not want to use module http
soup_present = True
soup_err = "Module newtorrents requires BeautifulSoup. Please install it from http://www.crummy.com/software/BeautifulSoup/ or from your distribution repository."

try:
    from BeautifulSoup import BeautifulSoup
except:
    log.warning(soup_err)
    soup_present = False

class ResolvePirateBay:
    """PirateBay resolver."""

    def register(self, manager, parser):
        manager.register_resolver(instance=self, resolvable=self.resolvable, resolve=self.resolve)

    def resolvable(self, feed, entry):
        url = entry['url']
        if url.startswith('http://thepiratebay.org') and not url.endswith('.torrent'):
            return True
        else:
            return False
        
    def resolve(self, feed, entry):
        if not soup_present:
            log.error(soup_err)
            return
        
        try:
            page = urllib2.urlopen(entry['url'])
            soup = BeautifulSoup(page)
            tag_div = soup.find("div", attrs={"class":"download"})
            tag_a = tag_div.find("a")
            torrent_url = tag_a.get('href')
            entry['url'] = torrent_url
            return True
        except Exception, e:
            logging.exception(e)
            return False