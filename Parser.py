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

from bs4 import BeautifulSoup
import re
import logging
import datetime

class Parser:
    """Parser for Parsering the data
    """
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        pass

    def getTopNews(self, file):
        """
        input:a price home file contains price pics 
        output: get top news containing today's price pics 
        """        
        content = open(file, 'r')
        soup = BeautifulSoup(content)

        topPriceNews = {}
        h4s = soup.find_all('h4')

        year = datetime.date.today().strftime("%Y")
        p = re.compile(r'.*(\d+)月(\d+)日.*')
        for h4 in h4s:
            content = h4.get_text().encode('utf-8')
            if '置顶' in content and '月' in content:
                time = year + '-' + p.match(content).group(1) + '-' + p.match(content).group(2)
                topPriceNews[time] = h4.find('a').get('href')
        return topPriceNews
    # end getTopNews()

    def getPricePicsUrl(self, file):
        """
        input:a price home file contains price pics url
        output: pics url
        """        
        content = open(file, 'r')
        soup = BeautifulSoup(content)

        pricePicsUrl = {}
        entry = soup.find("div", "entry typo")
        imgs = entry.find_all('img')
        if len(imgs) == 1:
            pricePicsUrl['morning'] = imgs[0].get('src')
        else:
            pricePicsUrl['morning'] = imgs[0].get('src')
            pricePicsUrl['afternoon'] = imgs[1].get('src')

        return pricePicsUrl
    # end getTopNews()
    # 
    def getTotalPageNum(self, file):
        """
        input:a file contains 共17页
        output: 17
        """
        content = open(file, 'r')
        soup = BeautifulSoup(content)
        p = re.compile(r'\D*(\d+)\D*')
        spans = soup.find_all("span", "sum")
        if spans:
            return int(p.match(spans[0].string).group(1))
        else:
            return -1
    # end getTotalPageNum()

    def getPerPageNum(self, file):
        """
        input:a home file contains 
        <a href="/tv_genre.jsp?type=tvcolumn&amp;category=3&amp;satellite=false&amp;alltime=false&amp;start=20">2</a>
        output: 20
        """        
        content = open(file, 'r')
        soup = BeautifulSoup(content)
        p = re.compile(r'.*=(\d*)$')
        for link in soup.find_all('a'):
            if "start" in link.get('href'):
                return int(p.match(link.get('href')).group(1))
        return -1
    # end getPerPageNum()

    def _has_itemprop(self, tag):
        return tag.has_attr('itemprop')

    def writeTvProgramsInfoIntoTables(self, srcFile, dstFile, conn, table, cateName):
        """
        srcFile:a file contains many tvcolumns 
        dstFile:write tvcolumns into tables stored in the MySQLdb
        fields: 
            link,cateName,name,pic,host,statistics,schedule,commentlink
        """  
        src = open(srcFile, 'r')
        soup = BeautifulSoup(src)
        
        commentsUrlDict = {}

        lis = soup.find_all("li", "clear")
        for li in lis:
            schedule = li.find("div", "chns").get_text().encode('utf-8')
            if len(schedule) > 2000:                            #skip tvProgramsInfo with schedule length > 2000
                print 'schedule length larger than 2000'
                continue   

            tvProgramsUrl = (li.find("a", "obj14").attrs)['href']

            link = tvProgramsUrl

            tvProgramsName = li.find("a", "obj14").string.encode('utf-8')
            name = tvProgramsName

            if li.find("img", "box2 tvc"):                      #tvPrograms lists in tvcloumn
                pic = (li.find("img", "box2 tvc").attrs)['src']
            elif li.find("img", "box2"):                        #tvPrograms lists in drama
                pic = (li.find("img", "box2").attrs)['src']
            else:
                pic = ''

            if li.find(self._has_itemprop):
                hostTags = li.find_all(self._has_itemprop)
                host = ''
                for hostTag in hostTags:
                    host += hostTag.string.encode('utf-8') + ' '
            else:
                host = ''

            statisticInfo = li.find("div", "gray mt5").get_text().encode('utf-8')
            statistics = statisticInfo

            commentlink = tvProgramsUrl + "/comments"

            dst = open(dstFile, "a+")
            if tvProgramsUrl+':'+cateName in dst.read():                     #skip same tvProgramsInfo
                print 'same tvPrograms of cateName exists '
                continue
            else:
                logging.info('begin to write one tvProgram into table TvProgramsInfo, 节目类别:' + cateName + ',节目名称:' + name)
                # write info into table
                conn.insert(table, cate=cateName,link=link,name=name,pic=pic,host=host,statistics=statistics,schedule=schedule,commentlink=commentlink)
                conn.commit()
                logging.info('finishing writing one tvProgram into table TvProgramsInfo, 节目类别:' + cateName + ',节目名称:' + name)

                dst.write('-----------------------------\n')
                dst.write('节目链接/类别:' + tvProgramsUrl + ':' + cateName + "\n")

                p = re.compile('(\d+).*')
                commentsUrlDict[tvProgramsName] = tvProgramsUrl + "/comments " + p.match(statisticInfo.split()[1]).group(1)
            dst.close()

        src.close()
        
        return commentsUrlDict
    # end writeTvProgramsInfoIntoTables()
# end class Parser