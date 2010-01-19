# -*- coding: utf-8 -*-
#
# File: Searcher.py
#
# Copyright (c) 2009 by PloneGov
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# ------------------------------------------------------------------------------
from Products.CMFPlone.PloneBatch import Batch
from Products.PloneMeeting.utils import getDateFromRequest

# ------------------------------------------------------------------------------
class Searcher:
    '''The searcher creates and executes queries in the portal_catalog
       which are triggered by the user from the "advanced search" screen in
       PloneMeeting.'''
    def __init__(self, tool):
        self.tool = tool # The PloneMeeting tool.
        self.rq = self.tool.REQUEST # The Zope REQUEST object.
        self.meetingConfig = getattr(self.tool, self.rq.get('search_config'))
        self.keywordsQuery = None

    wrongKeywordChars = '?-+*()'
    def constructKeywordsQuery(self, keywords):
        '''From the p_keywords entered by the user, creates and returns a query
           that can be used to search a ZCTextIndex like 'Title' or
           'Description'.'''
        # Remove unwanted chars
        res = keywords.strip()
        if res == '*': res = ''
        for c in self.wrongKeywordChars: res = res.replace(c, ' ')
        if res: res = " AND ".join(res.split())+'*'
        return res

    def getMultiValue(self, paramName):
        '''Gets, from the request, a multi-valued element.'''
        res = self.rq.get(paramName, [])
        if isinstance(res, basestring): res = [res]
        return res

    def getItemSearchParams(self, mainParams, dateInterval):
        '''Adds to dict p_mainParams the parameters which are specific for
           performing (an) item-specific query(ies) in the portal_catalog.'''
        res = mainParams.copy()
        res['portal_type'] = self.meetingConfig.getItemTypeName()
        res['modified'] = {'query': dateInterval, 'range':'minmax'}
        res['sort_on'] = 'modified'
        if self.keywordsQuery:
            # What fields need to be queried?
            kTargets = self.getMultiValue('item_keywords_target')
            if ('search_item_titles' in kTargets) and \
               ('search_item_decisions' in kTargets):
                # In this special case we will search in SearchableText only,
                # because its content corresponds to union of indexes Text,
                # Description and getDecision (and a little bit more...)
                # This is more efficient than performing several queries and
                # merging results (as done in the following cases).
                res['SearchableText'] = self.keywordsQuery
            else:
                if 'search_item_titles' in kTargets:
                    # Search among item's title and description
                    res['Title'] = self.keywordsQuery
                    res['Description'] = self.keywordsQuery
                if 'search_item_decisions' in kTargets:
                    res['getDecision'] = self.keywordsQuery
        proposingGroups = self.getMultiValue('proposingGroups')
        if proposingGroups:
            res['getProposingGroup'] = proposingGroups
        associatedGroups = tuple(self.getMultiValue('associatedGroups'))
        if associatedGroups:
            operator = self.rq.get('ag_operator', 'and')
            if (operator == 'or') and (len(associatedGroups) > 1):
                associatedGroups = ' OR '.join(associatedGroups)
            res['getAssociatedGroups'] = associatedGroups
        categories = self.getMultiValue('categories')
        if categories:
            res['getCategory'] = categories
        classifiers = self.getMultiValue('classifiers')
        if classifiers:
            res['getRawClassifier'] = classifiers
        return res

    def getMeetingSearchParams(self, mainParams, dateInterval):
        '''Adds to dict p_mainParams the parameters which are specific for
           performing (a) meeting-specific query(ies) in the portal_catalog.'''
        res = mainParams.copy()
        res['portal_type'] = self.meetingConfig.getMeetingTypeName()
        res['getDate'] = {'query': dateInterval, 'range':'minmax'}
        res['sort_on'] = 'getDate'
        if self.keywordsQuery: res['Title'] = self.keywordsQuery
        return res

    def getAnnexSearchParams(self, mainParams, dateInterval):
        '''Adds to dict p_mainParams the parameters which are specific for
           performing (an) annex-specific query(ies) in the portal_catalog.'''
        res = mainParams.copy()
        res['portal_type'] = 'MeetingFile'
        res['modified'] = {'query': dateInterval, 'range':'minmax'}
        res['sort_on'] = 'modified'
        if self.keywordsQuery:
            # Search among annex title and content
            res['Title'] = self.keywordsQuery
            res['getExtractedText'] = self.keywordsQuery
        return res

    def queryCatalog(self, params):
        '''Performs a single query catalog.'''
        return self.tool.portal_catalog(**params)[:params['sort_limit']]

    def mergeResults(self, results, sortKey):
        '''p_results contains several lists of brains that we need to merge.
           We need to take the p_sortKey into account.'''
        res = []
        moreBrains = True
        nextIndexes = [0] * len(results)
        nextCandidates = {} # ~{i_listNumber: brain}~
        while moreBrains:
            # Compute next candidates
            nextCandidates.clear()
            i = -1
            for nextIndex in nextIndexes:
                i += 1
                brainsList = results[i]
                if nextIndex < len(brainsList):
                    # There is at least one more candidate in this list
                    nextCandidates[i] = brainsList[nextIndex]
            if not nextCandidates:
                moreBrains = False
            else:
                # Compute the winner among all candidates
                winner = None
                winnerListNumber = None
                for listNumber, candidate in nextCandidates.iteritems():
                    if not winner:
                        winner = candidate
                        winnerListNumber = listNumber
                    else:
                        # Compare the current winner to this candidate
                        winnerKey = getattr(winner, sortKey)
                        candidateKey = getattr(candidate, sortKey)
                        if winnerKey < candidateKey:
                            winner = candidate
                            winnerListNumber = listNumber
                        if (winnerKey == candidateKey) and \
                           (winner.id == candidate.id):
                            # We can be reasonably sure they represent the same
                            # object. Skip this (duplicate) candidate.
                            nextIndexes[listNumber] += 1
                # Add the winner to the result and prepare next iteration
                res.append(winner)
                nextIndexes[winnerListNumber] += 1
        return res

    def searchItems(self, params):
        '''Executes the portal_catalog search(es) for querying items, and
           returns corresponding brains.'''
        res = [] # We will begin by storing here a list of lists of brains.
        # Indeed, several queries may be performed.
        if params.has_key('Title'):
            # Execute the Title-related query
            tParams = params.copy(); del tParams['Description']
            if tParams.has_key('getDecision'): del tParams['getDecision']
            res.append(self.queryCatalog(tParams))
            del params['Title'] # The title has been "consumed".
            # Execute the Description-related query
            dParams = params.copy()
            if dParams.has_key('getDecision'): del dParams['getDecision']
            res.append(self.queryCatalog(dParams))
            del params['Description'] # The description has been "consumed".
        if params.has_key('getDecision'):
            res.append(self.queryCatalog(params))
        # No result yet? Execute the single query from p_params.
        if not res:
            res.append(self.queryCatalog(params))
        if len(res) == 1: return res[0]
        else:
            return self.mergeResults(res, 'modified')[:params['sort_limit']]

    def searchMeetings(self, params):
        '''Executes the portal_catalog search(es) for querying meetings, and
           returns corresponding brains.'''
        res = self.tool.portal_catalog(**params)[:params['sort_limit']]
        return res

    def searchAnnexes(self, params):
        '''Executes the portal_catalog search(es) for querying annexes, and
           returns corresponding brains.'''
        res = [] # We will begin by storing here a list of lists of brains.
        # Indeed, several queries may be performed.
        if params.has_key('Title'):
            # Execute the Title-related query
            tParams = params.copy(); del tParams['getExtractedText']
            res.append(self.queryCatalog(tParams))
            del params['Title'] # The title has been "consumed".
            # Execute the extractedText-related query
            res.append(self.queryCatalog(params))
        # No result yet? Execute the single query from p_params.
        if not res:
            res.append(self.queryCatalog(params))
        if len(res) == 1: return res[0]
        else:
            return self.mergeResults(res, 'modified')[:params['sort_limit']]

    def run(self):
        '''Creates and executes queries and returns the result.'''
        rq = self.rq
        searchTypes = rq.get('search_types', [])
        # Determine batch sizes. Because we use standard Plone navigation macro
        # and we have potentially several paginated query results on the same
        # page, we can't remember the current page of every list. So we simply
        # get the batch start of the list that the user is currently browsing
        # and we reinitialize other lists to batch start 0. This avoids
        # re-writing the Plone navigation macro and should satisfy 99% of the
        # needs.
        currentBatchMetaType = rq.get('resultMetaType', None)
        itemBatchStart = 0
        meetingBatchStart = 0
        annexBatchStart = 0
        if currentBatchMetaType == 'MeetingItem':
            itemBatchStart = rq.get('b_start', 0)
        elif currentBatchMetaType == 'Meeting':
            meetingBatchStart = rq.get('b_start', 0)
        elif currentBatchMetaType == 'MeetingFile':
            annexBatchStart = rq.get('b_start', 0)
        # Determine "from" and "to" dates that determine the time period for
        # the search.
        fromDate = getDateFromRequest(rq.get('from_day'),
            rq.get('from_month'), rq.get('from_year'), start=True)
        toDate = getDateFromRequest(rq.get('to_day'),
            rq.get('to_month'), rq.get('to_year'), start=False)
        # Prepare the keywords query if keywords have been entered by the user
        if rq.get('keywords', None):
            self.keywordsQuery = self.constructKeywordsQuery(rq.get('keywords'))
        # Prepare main search parameters.
        mainParams = {'sort_limit': self.tool.getMaxSearchResults(),
                      'sort_order': 'reverse'}
        itemResult = ()
        meetingResult = ()
        annexResult = ()
        if 'search_type_items' in searchTypes:
            params = self.getItemSearchParams(mainParams, [fromDate, toDate])
            itemBrains = self.searchItems(params)
            bSize = self.tool.getMaxShownFoundItems()
            itemResult = Batch(itemBrains, bSize, itemBatchStart, orphan=0)
        if 'search_type_meetings' in searchTypes:
            params = self.getMeetingSearchParams(mainParams, [fromDate, toDate])
            meetingBrains = self.searchMeetings(params)
            bSize = self.tool.getMaxShownFoundMeetings()
            meetingResult= Batch(meetingBrains,bSize,meetingBatchStart,orphan=0)
        if 'search_type_annexes' in searchTypes:
            params = self.getAnnexSearchParams(mainParams, [fromDate, toDate])
            annexBrains = self.searchAnnexes(params)
            bSize = self.tool.getMaxShownFoundAnnexes()
            annexResult = Batch(annexBrains, bSize, annexBatchStart, orphan=0)
        # Result: 2nd elem: item brains, 3rd elem: meeting brains.
        return [self.meetingConfig, itemResult, meetingResult, annexResult]
# ------------------------------------------------------------------------------
