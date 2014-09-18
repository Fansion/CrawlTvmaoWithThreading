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

import os

# constants
#------------------------------
_bools = ['false', 'true']
# /home/frank/Python/crawller/crawlTvmao/TvProgramsInfo/
_tvProgramsInfoBasePath = os.path.abspath('.') + '/TvProgramsInfo/'         #tvProgramsInfo folder
_tvProgramsCommentsBasePath = os.path.abspath('.') + '/TvProgramsComments/' #tvProgramsComments folder
_homeWebPageDir = os.path.abspath('.') + '/homeWebPage/'                       #homeWebPage folder
_pagingWebPageDir = os.path.abspath('.') + '/pagingWebPage/'                   #pagingWebPage folder
_commentsHomeWebPageDir = os.path.abspath('.') + '/commentsHomeWebPage/'                   #commentsHomeWebPage folder
_websiteUrlBase = 'http://www.tvmao.com'
_cateUrl = 'http://tvmao.com/tv_genre.jsp?type={type}&category={category}&satellite=false&alltime='
#------------------------------


# local mysql db
#------------------------------
dbHost = 'localhost'
dbUser = 'root'
dbPassword = 'root'
dbName = 'TvProgramsTest2'
#------------------------------


# tv programs cates to be crawlled
#------------------------------
tvProgramsCates = { 
                    'tvcolumn 3' : '综艺',
                    'drama 2' : '电视剧',  # 19    武侠| 21      穿越 | 2        战争
                    'movie 0' : '电影',
                    'drama 24' : '少儿',
                    'tvcolumn 9' : '少儿',
                    'movie 27' : '少儿',
                    'tvcolumn 2' : '体育',
                    'tvcolumn 4' : '财经',
                    'tvcolumn 10' : '生活',
                    'tvcolumn 1' : '新闻',
                    'tvcolumn 6' : '科教'                        
                    }    #不同cate下可有同一个tvprogram
#------------------------------


# constants for Spider
#------------------------------
timeout = 5
fetched_url = 0
failed_url = 0
timeout_url = 0
trytoomany_url =0
other_url = 0
max_try_times = 5
total_url = 0

DNSCache = {}				# cache dns(domain name->IP addr) to reduce time cost

RESULTOTHER = 0 			#Other faults
RESULTFETCHED = 1 			#success
RESULTCANNOTFIND = 2 		#can not find 404
RESULTTIMEOUT = 3 			#timeout
RESULTTRYTOOMANY = 4 		#too many tries
#------------------------------




