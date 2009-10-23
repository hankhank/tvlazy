#!/usr/bin/python

import os
import sys
from nose.tools import *
from nose.plugins.attrib import attr
from flexget.manager import Manager, Session
from flexget.plugin import get_plugin_by_name, load_plugins
from flexget.options import OptionParser
from flexget.feed import Feed
from flexget import initialize_logging
import yaml

test_options = None

plugins_loaded = False
def setup_once():
    global plugins_loaded, test_options
    if not plugins_loaded:
        initialize_logging(True)
        parser = OptionParser(True)
        load_plugins(parser)
        test_options = parser.parse_args()[0]
        plugins_loaded = True

class MockManager(Manager):
    unit_test = True
    def __init__(self, config_text, config_name):
        self.config_text = config_text
        self.config_name = config_name
        Manager.__init__(self, test_options)

    def load_config(self):
        try:
            self.config = yaml.safe_load(self.config_text)
            self.config_base = os.path.dirname(os.path.abspath(sys.path[0]))
        except Exception, e:
            print 'Invalid configuration'
            raise

class FlexGetBase(object):
    __yaml__ = """# Yaml goes here"""

    def setup(self):
        """Set up test env"""
        setup_once()
        self.manager = MockManager(self.__yaml__, self.__class__.__name__)

    def teardown(self):
        try:
            self.feed.session.close()
        except:
            pass
        
    setUp = setup
    tearDown = teardown

    def execute_feed(self, name):
        """Use to execute one test feed from config"""
        config = self.manager.config['feeds'][name]
        if hasattr(self, 'feed'):
            if hasattr(self, 'session'):
                self.feed.session.close() # pylint: disable-msg=E0203
        self.feed = Feed(self.manager, name, config)
        self.feed.session = Session()
        self.feed.process_start()
        self.feed.execute()
        self.feed.process_end()
        self.feed.session.commit()
        
    def dump(self):
        """Helper method for debugging"""
        from flexget.utils.tools import sanitize
        #entries = sanitize(self.feed.entries)
        #accepted = sanitize(self.feed.accepted)
        #rejected = sanitize(self.feed.rejected)
        print '-- ENTRIES: -----------------------------------------------------'
        #print yaml.safe_dump(entries)
        print self.feed.entries
        print '-- ACCEPTED: ----------------------------------------------------'
        #print yaml.safe_dump(accepted)
        print self.feed.accepted
        print '-- REJECTED: ----------------------------------------------------'
        #print yaml.safe_dump(rejected)
        print self.feed.rejected

class TestRegexp(FlexGetBase):

    __yaml__ = """
        global:
          input_mock:
            - {title: 'regexp1', 'imdb_score': 5}
            - {title: 'regexp2', 'bool_attr': true}
            - {title: 'regexp3', 'imdb_score': 5}
            - {title: 'regexp4', 'imdb_score': 5}
            - {title: 'regexp5', 'imdb_score': 5}
            - {title: 'regexp6', 'imdb_score': 5}
            - {title: 'regexp7', 'imdb_score': 5}
            - {title: 'regexp8', 'imdb_score': 5}
            - {title: 'regexp9', 'imdb_score': 5}
          seen: false


        feeds:
          # test accepting, setting custom path (both ways), test not (secondary regexp)
          test_accept:
            regexp:
              accept:
                - regexp1
                - regexp2: ~/custom_path/2/
                - regexp3:
                    path: ~/custom_path/3/
                - regexp4:
                    not:
                      - exp4
                      
          # test rejecting        
          test_reject:
            regexp:
              reject:
                - regexp1
                
          # test rest
          test_rest:
            regexp:
              accept:
                - regexp1
              rest: reject
              
              
          # test excluding
          test_excluding:
            regexp:
              accept_excluding:
                - regexp1
                
          # test from
          test_from:
            regexp:
              accept:
                - localhost:
                    from:
                      - title
    """
    def test_accept(self):
        self.execute_feed('test_accept')
        assert self.feed.find_entry('accepted', title='regexp1'), 'regexp1 should have been accepted'
        assert self.feed.find_entry('accepted', title='regexp2'), 'regexp2 should have been accepted'
        assert self.feed.find_entry('accepted', title='regexp3'), 'regexp3 should have been accepted'
        assert self.feed.find_entry('entries', title='regexp4'), 'regexp4 should have been left'
        assert self.feed.find_entry('accepted', title='regexp2', path='~/custom_path/2/'), 'regexp2 should have been accepter with custom path'
        assert self.feed.find_entry('accepted', title='regexp3', path='~/custom_path/3/'), 'regexp3 should have been accepter with custom path'
            
    def test_reject(self):
        self.execute_feed('test_reject')
        assert self.feed.find_entry('rejected', title='regexp1'), 'regexp1 should have been rejected'

    def test_rest(self):
        self.execute_feed('test_rest')
        assert self.feed.find_entry('accepted', title='regexp1'), 'regexp1 should have been accepted'
        assert self.feed.find_entry('rejected', title='regexp3'), 'regexp3 should have been rejected'
            
    def test_excluding(self):
        self.execute_feed('test_excluding')
        assert not self.feed.find_entry('accepted', title='regexp1'), 'regexp1 should not have been accepted'
        assert self.feed.find_entry('accepted', title='regexp2'), 'regexp2 should have been accepted'
        assert self.feed.find_entry('accepted', title='regexp3'), 'regexp3 should have been accepted'

    def test_from(self):
        self.execute_feed('test_from')
        assert not self.feed.accepted, 'should not have accepted anything'
        

class TestDisableBuiltins(FlexGetBase):
    """
        Quick a hack, test disable functionality by checking if seen filtering (builtin) is working
    """

    __yaml__ = """
        feeds:
            test:
                input_mock:
                    - {title: 'dupe1', url: 'http://localhost/dupe', 'imdb_score': 5}
                    - {title: 'dupe2', url: 'http://localhost/dupe', 'imdb_score': 5}
                disable_builtins: true 

            test2:
                input_mock:
                    - {title: 'dupe1', url: 'http://localhost/dupe', 'imdb_score': 5, description: 'http://www.imdb.com/title/tt0409459/'}
                    - {title: 'dupe2', url: 'http://localhost/dupe', 'imdb_score': 5}
                disable_builtins:
                    - seen
                    - cli_config
    """
    def test_disable_builtins(self):
        self.execute_feed('test')
        assert self.feed.find_entry(title='dupe1') and self.feed.find_entry(title='dupe2'), 'disable_builtins is not working?'


        
class TestInputHtml(FlexGetBase):

    __yaml__ = """
        feeds:
          test:
            html: http://download.flexget.com/
    """

    def test_parsing(self):
        self.execute_feed('test')
        assert self.feed.entries, 'did not produce entries'

class TestPriority(FlexGetBase):

    __yaml__ = """
        feeds:
          test:
            input_mock:
              - {title: 'Smoke'}
            accept_all: true
            priority:
              accept_all: 100
    """

    def test_smoke(self):
        self.execute_feed('test')
        assert self.feed.entries, 'no entries created'
        
        
class TestManipulate(FlexGetBase):

    __yaml__ = """
        feeds:
          test:
            input_mock:
              - {title: '[1234]foobar'}
            manipulate:
              cleaned:
                from: title
                regexp: \[\d\d\d\d\](.*)
    """
    
    def test_clean(self):
        self.execute_feed('test')
        assert self.feed.find_entry(cleaned='foobar'), 'title not cleaned'


class TestImmortal(FlexGetBase):

    __yaml__ = """
        feeds:
          test:
            input_mock:
              - {title: 'title1', immortal: yes}
              - {title: 'title2'}
            regexp:
              reject:
                - .*
    """
    
    def test_immortal(self):
        self.execute_feed('test')
        assert self.feed.find_entry(title='title1'), 'rejected immortal entry'
        assert not self.feed.find_entry(title='title2'), 'did not reject mortal'

            
class TestDownload(FlexGetBase):
    
    __yaml__ = """
        feeds:
          test:
            input_mock:
              - {title: 'README', url: 'http://svn.flexget.com/trunk/bootstrap.py', 'filename': 'flexget_test_data'}
            accept_all: true
            download: 
              path: ~/
              fail_html: no
    """
    
    def tearDown(self):
        FlexGetBase.tearDown(self)
        if hasattr(self, 'testfile') and os.path.exists(self.testfile):
            os.remove(self.testfile)
        temp_dir = os.path.join(self.manager.config_base, 'temp')
        if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
            os.rmdir(temp_dir)

    @attr(online=True)
    def test_download(self):
        self.testfile = os.path.expanduser('~/flexget_test_data.ksh') # note: what the hell is .ksh and where it comes from?
        if os.path.exists(self.testfile):
            os.remove(self.testfile)
        # executes feed and downloads the file
        self.execute_feed('test')
        assert os.path.exists(self.testfile), 'download file does not exists'


class TestMetainfoQuality(FlexGetBase):

    __yaml__ = """
        feeds:
          test:
            input_mock:
              - {title: 'FooBar.S01E02.720p.HDTV'}
    """

    def test_quality(self):
        self.execute_feed('test')
        entry = self.feed.find_entry(title='FooBar.S01E02.720p.HDTV')
        assert entry, 'entry not found?'
        assert 'quality' in entry, 'failed to pick up quality'
        assert entry['quality'] == '720p', 'picked up wrong quality'




