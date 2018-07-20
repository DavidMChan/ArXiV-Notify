#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ArXiV Notify script
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright David Chan, 2018


# HTML Request sending and parsing
import urllib
from urllib import request
import requests
from xml.etree import ElementTree

# Import time utilities for handling the time values
import datetime
import dateutil.parser
import time

# Import the config parser
import configparse


## Build an ArXiV API Query which will query for the key
def build_query(queries, page, num_elements):
    query = "http://export.arxiv.org/api/query?search_query="
    search_element = ""
    if len(queries) == 0:
        search_element = "\"\""
    for i in range(len(queries)):
        search_element= search_element + "\"{}\"".format(urllib.parse.quote(str(queries[i])))
        if i+1 != len(queries):
            search_element = search_element + "+OR+"
    suffix = "&sortBy=lastUpdatedDate&sortOrder=descending&start={}&max_results={}".format(str(page), str(num_elements))
    return query + search_element + suffix

## Fetch the articles which are up to date
# that is, have been updated in the last day
def fetch_queries(queries, query_time):
    do_continue = True
    current_page = 0        # Which current page we are on
    pager_interval = 30     # How many articles to fetch at once
    fetched_data = []       # Each of the articles, their abstracts, and links

    while do_continue:
        # Fetch the next page of articles
        q = build_query(queries, current_page*pager_interval, pager_interval)
        query_page = urllib.request.urlopen(q)
        # Convert to a string and parse
        query_bytes = query_page.read()
        query_data = query_bytes.decode("utf8")
        query_page.close()
        page_root = ElementTree.fromstring(query_data)
        articles = page_root.findall("{http://www.w3.org/2005/Atom}entry")
        yesterday = dateutil.parser.parse(page_root.findtext("{http://www.w3.org/2005/Atom}updated")) - datetime.timedelta(days=int(query_time))
        
        # We put this sleep in to coform to the ArXiV bot standards
        time.sleep(3)

        # Build up the dataset of articles that we fetched
        for article in articles:
            link = article.findtext('{http://www.w3.org/2005/Atom}id')
            title = article.findtext('{http://www.w3.org/2005/Atom}title')
            abstract = article.findtext('{http://www.w3.org/2005/Atom}summary')
            date = article.findtext('{http://www.w3.org/2005/Atom}updated')
            datetime_obj  = dateutil.parser.parse(date)
            
            # If the published articles is too old - we're done looking.
            if datetime_obj < yesterday:
                do_continue = False
                break

            # Otherwise add the article
            fetched_data.append((title, link, abstract, datetime_obj))
        current_page += 1

    return fetched_data

## 1. Parse the Config File
CFG = configparse.parse('arxivnotify.cfg')

#  Check to see if any confiuration values are missing
if 'KEYWORD' not in CFG:
    raise ValueError("No keywords in the configuration file! Add one or more keywords using the \'KEYWORD\' field in the config file")
if type(CFG['KEYWORD']) is not list:
    # If there is only one keyword, make it into a list
    CFG['KEYWORD'] = [CFG['KEYWORD']]
if 'HISTORY_DAYS' not in CFG:
    print("WARNING: No history length set in the configuration. Setting to default of 1 day.")
    CFG['HISTORY_DAYS'] = '1'
if 'MAILGUN_ROOT' not in CFG:
    raise ValueError("No mailgun root specified! Specity the mailgun root using the \'MAILGUN_ROOT\' field in the config file")
if 'MAILGUN_API_KEY' not in CFG:
    raise ValueError("No mailgun API key specified! Specity the mailgun root using the \'MAILGUN_API_KEY\' field in the config file")
if 'MAILGUN_FROM' not in CFG:
    raise ValueError("No \'From Email\' specified! Specity the \'From Email\' using the \'MAILGUN_FROM\' field in the config file")
if 'MAILGUN_TO' not in CFG:
    raise ValueError("No destination emails specified! Specity one or more destination emails using the \'MAILGUN_TO\' field in the config file")
if type(CFG['MAILGUN_TO']) is not list:
    # If there is only one destination meail, make it into a list
    CFG['MAILGUN_TO'] = [CFG['MAILGUN_TO']]



## 2. Build the HTML email by quering ArXiV
try:
    mail_subject = "ArXiVAI Bot Email - {}".format(datetime.date.today().strftime("%B %d, %Y"))
    html_output = "<h2> ArXiVAI Bot Email - {} </h2>\n".format(datetime.date.today().strftime("%B %d, %Y"))
    for keyword in CFG['KEYWORD']:
        print("Parsing Keyword: {}".format(keyword))
        queries = fetch_queries([keyword], CFG['HISTORY_DAYS'])
        html_output += "<h3>" + keyword + "</h3>\n"
        html_output += "<ul>\n"
        for q in queries:
            html_output += "<li>\n"
            html_output += "\t<b><u>{}</u></b>".format(q[0])
            html_output += "<br>\n"
            html_output += "<a href=\"{}\">{}</a>&nbsp&nbsp&nbsp&nbsp{}\n".format(q[1],q[1],str(q[3]))
            html_output += "<br>\n"
            html_output += "{}\n".format(q[2])
            html_output += "</li>\n"
            html_output += "<br>\n"
        html_output += "</ul>\n"
except:
    raise RuntimeError("There was an error fetching data from the ArXiV server! Check to make sure you are connected to the internet!")

## 3. Send the Emails
RETURN_VAL = None
try:
    for email in CFG['MAILGUN_TO']:
        RETURN_VAL = requests.post(CFG['MAILGUN_ROOT'] + "/messages",
            auth=("api", CFG['MAILGUN_API_KEY']),
            data={"from": CFG['MAILGUN_FROM'],
                    "to": email,
                    "subject": mail_subject,
                    "text": html_output,
                    "html": html_output})
        if RETURN_VAL.status_code != 200:
            raise RuntimeError("Mail Error: ", RETURN_VAL.text)
except:
    raise RuntimeError('Arxiv notifier bot wasn\'t able to send an email! Check your mailgun API key and Root. HTML ERROR: {} {}'.format(RETURN_VAL.status_code, RETURN_VAL.text))