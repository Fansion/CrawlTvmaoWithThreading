#!/usr/bin/env python
# -*- coding: utf-8 -*-
# # Copyright 2014 by Frank Fu <ustcfrank@icloud.com>
#
# All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software
# and its documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Frank Fu  not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# Frank Fu DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL Frank Fu BE LIABLE FOR
# ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#

__author__ = 'frank'

import socket
import conf


class ErrorTryTooManyTimes(Exception):
    """try too many times"""
    pass


class Error404(Exception):
    """Can not find the page."""
    pass


class ErrorOther(Exception):
    """Some other exception"""

    def __init__(self, code):
        print 'Code :', code
        pass


def _parse(url):
    """Parse a url to hostName+fileName"""
    try:
        u = url.strip().strip('\n').strip('\r').strip('\t')
        if u.startswith('http://'):
            u = u[7:]
        elif u.startswith('https://'):
            u = u[8:]
        if u.find(':80') > 0:
            p = u.index(':80')
            p2 = p + 3
        else:
            if u.find('/') > 0:
                p = u.index('/')
                p2 = p
            else:
                p = len(u)
                p2 = -1
        hostName = u[:p]
        if p2 > 0:
            fileName = u[p2:]
        else:
            fileName = '/'
        return hostName, fileName
    except Exception, e:
        print "Parse wrong : ", url
        print e


def _dealWithHttpHead(head):
    """deal with HTTP HEAD"""
    lines = head.splitlines()
    fstLine = lines[0]
    code = fstLine.split()[1]
    if code == '404':
        return code, None
    if code == '200':
        return code, None
    if code == '301' or code == '302':
        for line in lines[1:]:
            p = line.index(':')
            key = line[:p]
            if key == 'Location':
                return code, line[p + 2:]
    return code, None


class Spider:
    """spider for crawlling data from website
    """

    def __init__(self):
        pass

    def downWebPage(self, url, file, mode, tryTimes=0):
        """download webPage based on exact url, store webPage at file, mode can be append(a) or
         overwrite(w)
        """
        hostName, fileName = _parse(url)
        try:
            # To avoid too many tries .Try times can not be more than max_try_times
            if tryTimes >= conf.max_try_times:
                raise ErrorTryTooManyTimes
        except ErrorTryTooManyTimes:
            return conf.RESULTTRYTOOMANY, hostName + fileName
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # DNS cache
            if hostName in conf.DNSCache:
                addr = conf.DNSCache[hostName]
            else:
                addr = socket.gethostbyname(hostName)
                conf.DNSCache[hostName] = addr
            # connect to http server ,default port 80
            s.connect((addr, 80))
            msg = 'GET ' + fileName + ' HTTP/1.0\r\n'
            msg += 'Host: ' + hostName + '\r\n'
            msg += 'User-Agent:Frank Fu\r\n\r\n'
            webPage = None
            s.sendall(msg)
            first = True
            while True:
                msg = s.recv(40960)
                if not len(msg):
                    if webPage:
                        webPage.flush()
                        webPage.close()
                    break
                # Head information must be in the first recv buffer
                if first:
                    first = False
                    headPos = msg.index("\r\n\r\n")
                    code, other = _dealWithHttpHead(msg[:headPos])
                    if code == '200':
                        # conf.fetched_url += 1
                        webPage = open(file, mode)
                        webPage.writelines(msg[headPos + 4:])
                    elif code == '301' or code == '302':
                        # if code is 301 or 302 , try down again using redirect location
                        if other.startswith("http"):
                            hname, fname = _parse(other)
                            self.downWebPage(hname, fname, tryTimes + 1)  # try again
                        else:
                            self.downWebPage(hostName, other, tryTimes + 1)
                    elif code == '404':
                        raise Error404
                    else:
                        raise ErrorOther(code)
                else:
                    if webPage:
                        webPage.writelines(msg)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            return conf.RESULTFETCHED, hostName + fileName
        except Error404:
            return conf.RESULTCANNOTFIND, hostName + fileName
        except ErrorOther:
            return conf.RESULTOTHER, hostName + fileName
        except socket.timeout:
            return conf.RESULTTIMEOUT, hostName + fileName
        except Exception, e:
            return conf.RESULTOTHER, hostName + fileName

    def dealWithResult(self, ret, url):
        """Deal with the result of downWebPage"""
        conf.total_url += 1
        if ret == conf.RESULTFETCHED:
            conf.fetched_url += 1
            print conf.total_url, '\t fetched :', url
        if ret == conf.RESULTCANNOTFIND:
            conf.failed_url += 1
            print "Error 404 at : ", url
        if ret == conf.RESULTOTHER:
            conf.other_url += 1
            print "Error Undefined at : ", url
        if ret == conf.RESULTTIMEOUT:
            conf.timeout_url += 1
            print "Timeout ", url
        if ret == conf.RESULTTRYTOOMANY:
            conf.trytoomany_url += 1
            print "Try too many times at", url