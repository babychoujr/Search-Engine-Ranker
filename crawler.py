# Kim Lang #33791771
# Eric Chou #95408627
# Jianing Tong #50419612

# CS 121 Project #2
import logging
import re
from urllib.parse import urlparse, urljoin
from corpus import Corpus
import os
from lxml import html
from frontier import Frontier

logger = logging.getLogger(__name__)


class Crawler:
    """
    This class is responsible for scraping urls from the next available link in frontier and adding the scraped links to
    the frontier
    """

    def __init__(self, frontier):
        self.frontier = frontier
        self.corpus = Corpus()
        self.store_dynamicURL = dict()  # Dict of dynamic URLS as key, freq as value
        self.store_URLs = dict()  # Dict of all subdomains visited as key, query as value
        self.outputURL = ("", 0)    #contains the url with the most output links and the count of output links
        self.downloadedURLs = []    #list of downloaded URLs
        self.traps = set()          #set of all traps to prevent showing repeat traps

    def start_crawling(self):
        """
        This method starts the crawling process which is scraping urls from the next available link in frontier and adding
        the scraped links to the frontier
        """
        while self.frontier.has_next_url():
            url = self.frontier.get_next_url()
            self.downloadedURLs.append(url)
            logger.info("Fetching URL %s ... Fetched: %s, Queue size: %s", url, self.frontier.fetched,
                        len(self.frontier))
            url_data = self.fetch_url(url)

            for next_link in self.extract_next_links(url_data):
                if self.corpus.get_file_name(next_link) is not None:
                    if self.is_valid(next_link):                #if the link is valid it stores into the frontier
                        self.frontier.add_url(next_link)
                    elif self.is_valid(next_link) == False:     #if the link is not valid it stores into the trap set()
                        self.traps.add(next_link)               #the way to identify a trap
        for url in self.frontier.urls_queue:                    #loops through the urls in queue
            self.downloadedURLs.append(url)                     #puts the urls that are downloaded into our downloadedURLS list
        self.write_analytics("analytics.txt")                   #writes the analytics to the analytics.txt file

    #writes the analytics required into our analytics.txt file
    def write_analytics(self, filename):
        with open(filename, 'w') as f:                  #opens the file up
            f.write("#1: SUBDOMAINS" + "\n")            #writes all the subdomains from our store_URLs
            for key, value in self.store_URLs.items():  #and writes the number of links from the subdomains
                f.write(key + "\t" + str(len(value)) + '\n')
            f.write("\n" + "#2 URL: " + self.outputURL[0] + " has the most output links of " + str(#writes the url with the most output links and the #
                self.outputURL[1]) + "\n")
            f.write("#3: DOWNLOADED LINKS" + "\n")
            for url in self.downloadedURLs:             #loops through the downloaded links and writes into the file
                f.write(url + "\n")
            f.write("\n" + "TRAPS:" + "\n")
            for trap in self.traps:                     #loops through the traps and writes the traps into the file
                f.write(trap + "\n")
        f.close()

    def fetch_url(self, url):
        """
        This method, using the given url, should find the corresponding file in the corpus and return a dictionary
        containing the url, content of the file in binary format and the content size in bytes
        :param url: the url to be fetched
        :return: a dictionary containing the url, content and the size of the content. If the url does not
        exist in the corpus, a dictionary with content set to None and size set to 0 can be returned.
        """
        #base url data
        url_data = {
            "url": url,
            "content": None,
            "size": 0
        }
        filepath = self.corpus.get_file_name(url)  # gets looks up for a local file and sends the address
        if filepath == None:    # if there is no filepath, return base url_data
            return url_data
        url_data["size"] = os.path.getsize(filepath) # gets the size of file using the filepath
        with open(filepath, "rb") as f:               # opens up the file and reads the file into binary format
            data = f.read()                             # reading
            url_data["content"] = data                 #places all the contents of the file in binary format into the content of the dict
        f.close()                                     #closes the file after done reading
        if "?" in url:                               #checks if the url in the dictionary is a dynamic url
            dynamic_url = url.split("?")[0]          #splits the url and indexing the first part before the ?
            dynamic_freq = self.store_dynamicURL.get(dynamic_url, 0)        #gets the frequency of the current dynamic url
            self.store_dynamicURL[dynamic_url] = dynamic_freq + 1           #adds one to the current frequency of the dynamic_url

        # Keeps track of subdomain visited for Analytics
        url_split = url.split("/")                                          #splits the url
        if url_split[2] in self.store_URLs.keys():                          #url_split[2] == the subdomain part
            self.store_URLs[url_split[2]].add("/".join(url_split[3:]))      # adds the path into the value of store_URLs
        else:
            self.store_URLs[url_split[2]] = set()
            self.store_URLs[url_split[2]].add("/".join(url_split[3:]))

        return url_data                                                   #returns the dict with the url, content in binary form, and size of the file

    def extract_next_links(self, url_data):
        """
        The url_data coming from the fetch_url method will be given as a parameter to this method. url_data contains the
        fetched url, the url content in binary format, and the size of the content in bytes. This method should return a
        list of urls in their absolute form (some links in the content are relative and needs to be converted to the
        absolute form). Validation of links is done later via is_valid method. It is not required to remove duplicates
        that have already been fetched. The frontier takes care of that.

        Suggested library: lxml
        """
        outputLinks = []
        tree = html.fromstring(url_data["content"])             #html.fromstring() expects the content in bytes  tree contains the html file
        url_list = tree.xpath('//a/@href')                      #xpath() scrapes the html file and gives us all the links we want in a list
        base_domain = url_data["url"]                           #the fetched_url
        for sub_url in url_list:                                                #goes through the urllist
            if sub_url.startswith("http://") or sub_url.startswith("https://"): #if the link is an absolute form add into outputlinks
                outputLinks.append(str(sub_url))
            else:                                                               #if not in absolute form or anything else
                joined_url = urljoin(base_domain, sub_url)                      #first join url with the fetched url then add into outputlinks
                outputLinks.append(str(joined_url))                             #joins the query or path

        if self.outputURL[1] < len(url_list):                                   # adds the next link if it has more links than the one before
            self.outputURL = (url_data["url"], len(url_list))

        return outputLinks

    def is_valid(self, url):
        """
        Function returns True or False based on whether the url has to be fetched or not. This is a great place to
        filter out crawler traps. Duplicated urls will be taken care of by frontier. You don't need to check for duplication
        in this method
        """
        parsed = urlparse(url)
        url_breakdown = url.split('/')  # list of url split by '/'

        # Checks for URLs with repetitions in the query and
        # returns false if greater than 2.
        url_dict = dict()
        for word in url_breakdown:
            freq = url_dict.get(word, 0)
            url_dict[word] = freq + 1
        for value in url_dict.values():
            if value > 2:               #if there is more than 2 duplicates in the url, it is considered as a trap
                return False

        # Checks for URLs that are super long
        if len(url_breakdown[-1]) > 150: # checking if the path is extremely long
            return False

        # Checks for dynamic URLs that impede progress of crawler
        dynamic_url = url.split("?")[0]
        if dynamic_url in self.store_dynamicURL.keys() and self.store_dynamicURL[dynamic_url] > 20:  #checks if the dynamic url appears more than 20 times
            return False

        if parsed.scheme not in set(["http", "https"]):
            return False

        try:
            return ".ics.uci.edu" in parsed.hostname \
                   and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4" \
                                    + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                                    + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                                    + "|thmx|mso|arff|rtf|jar|csv" \
                                    + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower())

        except TypeError:
            print("TypeError for ", parsed)
            return False

