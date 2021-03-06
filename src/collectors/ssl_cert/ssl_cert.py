# coding=utf-8

"""
Collect statistics from a SSL certificate of a domain

#### Dependencies

 * socket
 * ssl
 * datetime

#### Usage
Add the collector config as :

enabled = True
ttl_multiplier = 2
path_suffix = ""
measure_collector_time = False
byte_unit = byte,
urls = list of comma seperated domain names without protocol (e.g. blueshoe.de)

Metrics are collected as :
    - servers.<hostname>.ssl_cert.<url>.days_left

    '.' chars are replaced by __, url looking like
       www.site.com is being replaced by
       www_site_com
"""

import socket
from datetime import datetime
from OpenSSL import SSL

import diamond.collector


def get_cert(host, port):
    """get certificate from remote host"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    context = SSL.Context(SSL.TLSv1_METHOD)
    conn = SSL.Connection(context, sock)
    conn.set_connect_state()
    conn.set_tlsext_host_name(host)
    conn.do_handshake()
    cert = conn.get_peer_certificate()
    conn.shutdown()
    return cert

def ssl_expiry_datetime(hostname):
    # ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'
    #
    # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    # conn = context.wrap_socket(
    #     socket.socket(socket.AF_INET),
    #     server_hostname=hostname,
    # )
    # # 3 second timeout because Lambda has runtime limitations
    # conn.settimeout(3.0)
    #
    # conn.connect((hostname, 443))
    # ssl_info = conn.getpeercert()
    # parse the string from the certificate into a Python datetime object
    return datetime.strptime(get_cert(hostname, 443).get_notAfter(), "%Y%m%d%H%M%SZ")


def ssl_valid_time_remaining(hostname):
    """Get the number of days left in a cert's lifetime."""
    expires = ssl_expiry_datetime(hostname)
    # logger.debug(
    #     "SSL cert for %s expires at %s",
    #     hostname, expires.isoformat()
    # )
    return expires - datetime.utcnow()


class SslCertCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(SslCertCollector, self).get_default_config_help()
        config_help.update({
            'urls': 'comma seperated list of urls'
        })
        return config_help

    def get_default_config(self):
        default_config = super(SslCertCollector, self).get_default_config()
        default_config['path'] = 'ssl_cert'
        default_config['urls'] = ['blueshoe.de']
        return default_config

    def collect(self):
        for url in self.config['urls']:
            self.log.debug("checking ssl_cert of %s", str(url))
            # remaining time of certificate
            remaining = ssl_valid_time_remaining(url)
            # parse url to metrics name
            metric_name = url.replace(
                '/', '_').replace(
                '.', '_').replace(
                '\\', '').replace(
                ':', '')
            self.publish_gauge(metric_name + '.days_left', remaining.days)
