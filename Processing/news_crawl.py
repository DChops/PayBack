# news content collection
import json
import logging
import time

import requests
from tqdm import tqdm
from newspaper import Article


# code sourced from  : https://github.com/KaiDMML/FakeNewsNet/blob/master/code/news_content_collection.py


def crawl_link_article(url):
    result_json = None

    try:
        if 'http' not in url:
            if url[0] == '/':
                url = url[1:]
            try:
                article = Article('http://' + url)
                article.download()
                time.sleep(2)
                article.parse()
                flag = True
            except:
                logging.exception("Exception in getting data from url {}".format(url))
                flag = False
                pass
            if flag == False:
                try:
                    article = Article('https://' + url)
                    article.download()
                    time.sleep(2)
                    article.parse()
                    flag = True
                except:
                    logging.exception("Exception in getting data from url {}".format(url))
                    flag = False
                    pass
            if flag == False:
                return None
        else:
            try:
                article = Article(url)
                article.download()
                time.sleep(2)
                article.parse()
            except:
                logging.exception("Exception in getting data from url {}".format(url))
                return None

        if not article.is_parsed:
            return None

        visible_text = article.text
        top_image = article.top_image
        images = article.images
        keywords = article.keywords
        authors = article.authors
        canonical_link = article.canonical_link
        title = article.title
        meta_data = article.meta_data
        movies = article.movies
        publish_date = article.publish_date
        source = article.source_url
        summary = article.summary

        result_json = {'url': url, 'text': visible_text, 'images': list(images), 'top_img': top_image,
                       'keywords': keywords,
                       'authors': authors, 'canonical_link': canonical_link, 'title': title, 'meta_data': meta_data,
                       'movies': movies, 'publish_date': get_epoch_time(publish_date), 'source': source,
                       'summary': summary}
    except:
        logging.exception("Exception in fetching article form URL : {}".format(url))

    return result_json


def get_epoch_time(time_obj):
    if time_obj:
        return time_obj.timestamp()

    return None


def get_web_archieve_results(search_url):
    try:
        archieve_url = "http://web.archive.org/cdx/search/cdx?url={}&output=json".format(search_url)

        response = requests.get(archieve_url)
        response_json = json.loads(response.content)

        response_json = response_json[1:]

        return response_json

    except:
        return None


def get_website_url_from_arhieve(url):
    """ Get the url from http://web.archive.org/ for the passed url if exists."""
    archieve_results = get_web_archieve_results(url)
    if archieve_results:
        modified_url = "https://web.archive.org/web/{}/{}".format(archieve_results[0][1], archieve_results[0][2])
        return modified_url
    else:
        return None


def crawl_news_article(url):
    news_article = crawl_link_article(url)

    # If the news article could not be fetched from original website, fetch from archieve if it exists.
    if news_article is None:
        archieve_url = get_website_url_from_arhieve(url)
        if archieve_url is not None:
            news_article = crawl_link_article(archieve_url)

    return news_article


def collect_news_articles(news_list):
    # create_dir(config.dump_location)
    # create_dir("{}/{}".format(config.dump_location, news_source))
    # create_dir("{}/{}/{}".format(config.dump_location, news_source, label))

    # save_dir = "{}/{}/{}".format(config.dump_location, news_source, label)

    for news in tqdm(news_list):
        # create_dir("{}/{}".format(save_dir, news.news_id))
        news_article = crawl_news_article(news)
        if news_article:
            return news_article

class NewsContentCollector():

    def __init__(self,news_urls=[]):
        self.news=[]
        self.news_urls = news_urls
    
    def add_news_urls(self,news_urls):
       self.news_urls = news_urls

    def collect_data(self):
        # for choice in self.news_urls:
            # news_list = self.load_news_file(choice)
        self.news =(collect_news_articles(self.news_urls))

        return self.news