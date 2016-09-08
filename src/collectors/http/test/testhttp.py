#!/usr/bin/python
# coding=utf-8
##########################################################################

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from mock import Mock
from mock import patch

from diamond.collector import Collector

from http import HttpCollector

##########################################################################


class TestHttpCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('HttpCollector', {
            'req_vhost': 'www.my_server.com',
            'req_urls_and_teststrings': ['http://www.my_server.com/', 'keep out']
        })

        self.collector = HttpCollector(config, None)

    def test_import(self):
        self.assertTrue(HttpCollector)

    @patch.object(Collector, 'publish')
    def test_should_work_with_real_data(self, publish_mock):
        patch_urlopen = patch('urllib2.urlopen', Mock(
            return_value=self.getFixture('index')))

        patch_urlopen.start()
        self.collector.collect()
        patch_urlopen.stop()

        metrics = {
            'http__www_my_server_com_.size': 150,
            'http__www_my_server_com_.teststring': 1
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany([publish_mock,
                                  ], metrics)

##########################################################################
if __name__ == "__main__":
    unittest.main()
