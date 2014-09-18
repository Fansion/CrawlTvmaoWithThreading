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

import logging
import os
import datetime
from pythonMysql import *
import Spider
import Parser
import threadPool
import conf
import utility
from bs4 import BeautifulSoup


class TvmaoCrawller:
    """main class of crawlling Tvmao
    """
    def _getCateHomeWebPageInfo(self, homeWebPageInfoFile):
        """store home url and path info into file
        """
        homeWebPageInfo = open(homeWebPageInfoFile, 'w')
        for urlParas, cateName in conf.tvProgramsCates.items():
            #make cateUrl of tvPrograms list webpage
            cateUrl = conf._cateUrl
            te, cy = urlParas.split()
            cateUrl = cateUrl.replace("{type}", te).replace("{category}", cy)

            cateHomeUrl = ''                            #home page url , page index = 0
            for _bool in conf._bools:
                cateHomeUrl = cateUrl + _bool
                cateHomePath = conf._homeWebPageDir + cateName + '-' + te + '-' \
                                + cy + '-' + _bool      #tmp file to get totalPageNum and  perPageNum
                homeWebPageInfo.write(cateHomeUrl + ' ' + cateHomePath + '\n')
        homeWebPageInfo.close()

    def _init(self, homeWebPageInfoFile):
        """cleanup, initialization
        """
        utility.remove(conf._tvProgramsInfoBasePath)          #remove old file and create empty folder
        utility.remove(conf._tvProgramsCommentsBasePath)
        utility.remove("homeWebPage")                         #remove "homeWebPage" dir
        utility.remove("pagingWebPage")                       #remove "pagingWebPage" dir
        utility.remove("commentsHomeWebPage")                 #remove "commentsHomeWeb" dir

        utility.remove("homeWebPageInfo")                     #remove "homeWebPageInfo"
        utility.remove("pagingWebPageInfo")                   #remove "pagingWebPageInfo"
        utility.remove("commentsHomeWebPageInfo")             #remove "commentsHomeWebPage"
        utility.remove("commentsPagingWebPageInfo")

        os.mkdir(conf._tvProgramsInfoBasePath)
        os.mkdir(conf._tvProgramsCommentsBasePath)
        os.mkdir("homeWebPage")
        os.mkdir("pagingWebPage")
        os.mkdir("commentsHomeWebPage")

        logging.basicConfig(level=logging.ERROR)

        self._getCateHomeWebPageInfo(homeWebPageInfoFile)   #get homepage url and path

    def __init__(self, dbUser, dbPassword, homeWebPageInfoFile):
        """constructor
        """
        self._init(homeWebPageInfoFile)
        self.spider = Spider.Spider()
        self.parser = Parser.Parser()
        self.conn = Connection(conf.dbHost, conf.dbName, user=dbUser, password=dbPassword)     #db instance

    def __del__(self):
        self.conn.close()

    def _callbackfunc(self, request, result):
        """deal with the result of callable function
        update statistics variables
        """
        self.spider.dealWithResult(result[0], result[1])

    def crawlWebPageUsingThreadPool(self, urlAndPathInfofile, threadNum):
        """get webPage with self defined 'Get' method and use thread pool to improve efficiency
        """

        dnsCache = conf.DNSCache
        reload(conf)
        conf.DNSCache = dnsCache

        urlAndPath = open(urlAndPathInfofile, 'r')
        start = datetime.datetime.now()

        main = threadPool.ThreadPool(threadNum)   #initialize pool with threadNum threads
        for line in urlAndPath:
            # print line
            url, path = line.split()
            try:                                  #make work request, choose callablefunc and callbackfunc                  
                req = threadPool.WorkRequest(self.spider.downWebPage, args=[url, path, 'w'], \
                                                kwds={},  callback=self._callbackfunc)
                main.putRequest(req)              #put work request into thread pool
            except Exception:
                print Exception.message
        while True:
            try:
                main.poll()                       #call func to deal with result returned after work thread process work request 
            except threadPool.NoResultsPending:
                print 'no pending results'
                break
            except Exception, e:
                print e

        end = datetime.datetime.now()        
        print '-'*20
        print "Start at :\t" , start    
        print "End at :\t" , end
        print "Total Cost :\t" , end - start
        print 'Total url :',conf.total_url
        print 'Total fetched :', conf.fetched_url
        print 'Lost url :', conf.total_url - conf.fetched_url
        print 'Error 404 :' ,conf.failed_url
        print 'Error timeout :',conf.timeout_url
        print 'Error Try too many times ' ,conf.trytoomany_url
        print 'Error Other faults ',conf.other_url
        print '-'*20
        main.stop()

    def getCatePagingInfo(self, homeWebPageInfoFile, catePagingUrlAndPathInfoFile):
        """store catePagingInfo  url and path info into file based on homePageInfo
        """
        homePageInfo = open(homeWebPageInfoFile, 'r')
        homePageInfoDict = {}
        for line in homePageInfo:
            url, path = line.split()
            homePageInfoDict[path] = url
        # print homePageInfoDict

        homeWebPageInfoFiles = os.listdir(conf._homeWebPageDir)         #get catePagingInfo based on homePageInfo
        catePagingInfo = open(catePagingUrlAndPathInfoFile, 'w')

        for homeWebPageInfoFile in homeWebPageInfoFiles:

            totalPageNum = self.parser.getTotalPageNum(conf._homeWebPageDir + homeWebPageInfoFile) #get totalPageNum of tvPrograms in cateName lists
            perPageNum = self.parser.getPerPageNum(conf._homeWebPageDir + homeWebPageInfoFile)     #get perPageNum
            if totalPageNum == -1 or perPageNum == -1:          
                totalPageNum = 1                                                                   #drama only has one page tvPrograms

            for pageIndex in range(totalPageNum):
                catePagingUrl = homePageInfoDict[conf._homeWebPageDir + homeWebPageInfoFile] + '&start=' +  str(pageIndex*perPageNum)                     #make tvPrograms paging url
                catePagingPath = conf._pagingWebPageDir + homeWebPageInfoFile + '-' + str(pageIndex)  #path for storing tvPrograms paging data
                catePagingInfo.write(catePagingUrl + ' ' + catePagingPath + '\n')
        catePagingInfo.close()

    def writeTvProgramsInfoIntoTables(self, commentsHomeWebPageInfoFile):
        """write TvProgramsInfo IntoTables
        and get comments home web page
        """
        pagingWebPageInfoFiles = os.listdir(conf._pagingWebPageDir)         #get pagingWebPageInfo based on homePageInfo
        commentsHomeWebPageInfo = open(commentsHomeWebPageInfoFile, 'w')
        for pagingWebPageInfoFile in pagingWebPageInfoFiles:
            cateName = pagingWebPageInfoFile.split('-')[0]
            srcFile = conf._pagingWebPageDir + pagingWebPageInfoFile
            dstFile = conf._tvProgramsInfoBasePath + cateName + '_infolists'
            commentsUrlDict = self.parser.writeTvProgramsInfoIntoTables(srcFile, dstFile, self.conn,
                                                      "TvProgramsInfo", cateName)
            #get comments homewebpage
            for tvProgramsName, commentsUrl in commentsUrlDict.items():
                commentsUrl, commentsNum = commentsUrl.split()
                if int(commentsNum):
                    if ' ' in tvProgramsName:
                        tvProgramsName = tvProgramsName.replace(' ', '-')
                    #conf._commentsHomeWebPageDir + commentsUrl + '0\n' represents comments home web page
                    commentsHomeWebPageInfo.write(conf._websiteUrlBase + commentsUrl + ' ' + conf._commentsHomeWebPageDir + tvProgramsName + '-0\n')
        commentsHomeWebPageInfo.close()

    def getCommentsPagingWebPageInfo(self, commentsPagingWebPageInfoFile):
        """get comments paging WebPage info based on comments home web page
        """
        commentsHomeWebPageInfoFiles = os.listdir(conf._commentsHomeWebPageDir)
        commentsPagingWebPageInfo = open(commentsPagingWebPageInfoFile, 'w')
        for commentsHomeWebPageInfoFile in commentsHomeWebPageInfoFiles:

            #if comments has more than more page, get comments tags for pages other than first page
            catePagingCommentsTotalPageNum = self.parser.getTotalPageNum(conf._commentsHomeWebPageDir + commentsHomeWebPageInfoFile)
            commentsHomePageInfo = open(conf._commentsHomeWebPageDir + commentsHomeWebPageInfoFile, 'r')
            soup = BeautifulSoup(commentsHomePageInfo)
            hasPageTag = soup.find("div", "page") 
            if hasPageTag:              #if comments has more than more page 
                catePagingCommentsPerPageNum = int(hasPageTag.attrs['ps'])
                catePagingCommentsBaseUrl = conf._websiteUrlBase + hasPageTag.attrs['data_url']    #comments data servlet url

                if catePagingCommentsTotalPageNum != -1 and catePagingCommentsPerPageNum != -1:
                    for pageIndex in range(1, catePagingCommentsTotalPageNum):
                        catePagingCommentsPagingUrl = catePagingCommentsBaseUrl + str(pageIndex*catePagingCommentsPerPageNum)         #comments data servlet url
                        commentsPagingWebPageInfo.write(catePagingCommentsPagingUrl + ' ' + conf._commentsHomeWebPageDir + commentsHomeWebPageInfoFile.replace('-0', '-'+str(pageIndex)) + '\n')
            commentsHomePageInfo.close()
        commentsPagingWebPageInfo.close()

    def writeTvProgramsCommentsIntoTables(self):
        """write TvPrograms comments IntoTables
        """
        # get nameCommenturlDict
        # 家有儿女3 /drama/MmlZUA==/comments
        # 西游记 /drama/KhwuaSc=/comments
        nameCommenturlDict = {}
        commentsHomeWebPageInfo = open("commentsHomeWebPageInfo", 'r')
        for line in commentsHomeWebPageInfo:
            url, name = line.split()
            nameCommenturlDict[(name[name.rfind('/')+1:]).replace('-0', '')] = url[url.find('com')+3:]


        commentsHomeWebPageInfoFiles = os.listdir(conf._commentsHomeWebPageDir)
        for commentsHomeWebPageInfoFile in commentsHomeWebPageInfoFiles:
            commentsHomePageInfo = open(conf._commentsHomeWebPageDir + commentsHomeWebPageInfoFile, 'r')
            if commentsHomeWebPageInfoFile.endswith('-0'):          #comment home page
                soup = BeautifulSoup(commentsHomePageInfo)
            else:
                soup = BeautifulSoup(commentsHomePageInfo.read().replace('\\"', '"').replace('\\/', '/'))
            commentTag = soup.find_all('ul', 'commentlist mt10')[0]

            allCommentsPath = conf._tvProgramsCommentsBasePath + commentsHomeWebPageInfoFile[:commentsHomeWebPageInfoFile.rfind('-')] + "_commentslists" 
            logging.info('begin to crawl comments')
            logging.info('...')
            allComments = open(allCommentsPath, 'a+')

            lis = commentTag.find_all('li')
            for li in lis:
                allComments.write('-----------------------------\n')
                
                # commentcontent, commentid, commenttime, commentlink
                content = '评论内容:'
                if li.find("p"):
                    content += li.find("p").string.encode('utf-8') + '\n' if li.find("p").string else '' + "\n"
                    commentcontent = li.find("p").string.encode('utf-8') if li.find("p").string else ''
                elif li.find("div","desc2"):
                    commentcontent = li.find("div","desc2").string.encode('utf-8') if li.find("div","desc2").string else ''
                    content += li.find("div","desc2").string.encode('utf-8') + '\n' if li.find("div","desc2").string else '' + "\n"
                else:
                    content += 'null\n'
                    commentcontent = ''

                ID = '评论ID:'
                if li.find("span", "gray"):
                    ID += li.find("span", "gray").string.encode('utf-8') + '\n' if li.find("span", "gray").string else '' + "\n"
                    commentid = li.find("span", "gray").string.encode('utf-8') if li.find("span", "gray").string else ''
                else:
                    ID += 'null\n'
                    commentid = ''

                time = '评论时间:'
                # print li.find("span", "lt gray ml10").string.encode('utf-8')
                if  li.find("span", "lt gray ml10"):
                    time += li.find("span", "lt gray ml10").string.encode('utf-8') + '\n' if li.find("span", "lt gray ml10").string else '' + "\n"
                    commenttime = li.find("span", "lt gray ml10").string.encode('utf-8') if li.find("span", "lt gray ml10").string else ''
                else:
                    time += 'null\n'
                    commenttime = ''
                commentsUrl = nameCommenturlDict[commentsHomeWebPageInfoFile[:commentsHomeWebPageInfoFile.rfind('-')]]
                link = '评论链接:' + commentsUrl + '\n'
                commentlink = commentsUrl

                #skip same comment, key length should not be more than 2000
                #here is a compromisement method
                text = allComments.read()
                if content in text and ID in text and time in text and link in text:
                    print 'same comment exists'
                    continue
                elif len(content) > 2000:
                    print 'comment length larger than 2000'
                    continue                                    
                else:
                    logging.info('begin to write one comment into table TvProgramsComments, 节目名称:' + commentsHomeWebPageInfoFile[:commentsHomeWebPageInfoFile.rfind('-')] + ',评论时间:' + commenttime)
                    # write info into table
                    self.conn.insert('TvProgramsComments', commentlink=commentlink,commentid=commentid,commenttime=commenttime,commentcontent=commentcontent)
                    self.conn.commit()
                    logging.info('finishing writing one comment into table TvProgramsComments, 节目名称:' + commentsHomeWebPageInfoFile[:commentsHomeWebPageInfoFile.rfind('-')] + ',评论时间:' + commenttime)

                    allComments.write(content)
                    allComments.write(ID)
                    allComments.write(time)
                    allComments.write(link)

                allComments.write('-----------------------------\n')
            # end for li in lis
            allComments.close()
            logging.info('finish crawlling comments')


if __name__ == '__main__':
    crawller = TvmaoCrawller(conf.dbUser, conf.dbPassword, "homeWebPageInfo")  #get homeWebPageInfoFiles to get pagingWebPageInfoFiles
    crawller.crawlWebPageUsingThreadPool("homeWebPageInfo", 40)
    crawller.getCatePagingInfo("homeWebPageInfo", "pagingWebPageInfo")
    crawller.crawlWebPageUsingThreadPool("pagingWebPageInfo", 20)
    crawller.writeTvProgramsInfoIntoTables("commentsHomeWebPageInfo")          #get comments home web page
    crawller.crawlWebPageUsingThreadPool("commentsHomeWebPageInfo", 20)
    crawller.getCommentsPagingWebPageInfo("commentsPagingWebPageInfo")         #get comments paging WebPage info
    crawller.crawlWebPageUsingThreadPool("commentsPagingWebPageInfo", 20)
    crawller.writeTvProgramsCommentsIntoTables()    