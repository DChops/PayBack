from networkx.drawing.nx_pydot import graphviz_layout
import random, tweepy
import pandas as pd
import numpy as np
import seaborn as sb
import matplotlib.pyplot as plt
import networkx as nx
import requests
import json
from pathlib import Path


# uimport funcitons from external scripts
import news_crawl


class Graph:
    """
    Class Implementation of a graph module to construct tweet propagation network graphs using news url
    """

    def __init__(self, url=None):
        self.consumer_key = "xxxxxxx"
        self.consumer_secret = "xxxxxxx"
        self.access_token_key = "xxxxxxx-xxxxxxx"
        self.access_token_secret = "xxxxxxx"
        self.bearer_token = "xxxxxxxxxxxxxxxxxxxxx"
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token_key, self.access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        self.client = tweepy.Client(
            self.bearer_token,
            self.consumer_key,
            self.consumer_secret,
            self.access_token_key,
            self.access_token_secret,
            wait_on_rate_limit=True,
        )
        self.retweet_graph = None
        self.full_graph = None
        self.url = url
        myfile = Path("data.json")
        myfile.touch(exist_ok=True)
        fp = open(myfile)
        self.nodes = json.load(fp)
        print(len(self.nodes))
        fp.close()

    # compute a graph from news url and get tweets from last 7-days
    def get_graph_of_news_url(self, news_url):

        # first we collect news from news url
        news_url = news_url
        newsCollector = news_crawl.NewsContentCollector([news_url])
        news_data = newsCollector.collect_data()

        # search twitter timeline last 7-days mentioning the news url
        data = self.api.search_tweets(q=news_url, count=1000)

        graphs = []

        for i in data:
            if not i.retweeted and not i.is_quote_status:

                G_news, nodes = self.get_graph_of_tweet(
                    i.id, retweet_count=i.retweet_count
                )
                graphs.append(G_news)

        # source node grpah news node added
        G = nx.DiGraph()
        G.add_node(0)

        graphs_combined = graphs.copy()
        graphs_combined.append(G)

        F = nx.compose_all(graphs_combined)
        for i in data:
            if not i.retweeted and not i.is_quote_status:
                F.add_edge(0, i.user.id)

        plt.figure(figsize=(16, 8))
        pos = graphviz_layout(F, prog="dot")

        nx.draw(F, pos, with_labels=False)
        plt.savefig("Graph.png", format="PNG")

        with open("data.json", "w") as fp:
            json.dump(self.nodes, fp)

        return F, news_data

    # for
    # compute a graph of tweet = all combined together
    def get_graph_of_tweet(self, tweet_id, nodes={}, retweet_count=-1):

        print("Calling lookup_statuses api")
        uid = self.api.lookup_statuses([tweet_id])[
            0
        ].user.id  # getting user id of the person who tweeted the cascade node
        if retweet_count != 0:
            print("Calling quote tweet api")
            q, u = self.get_all_quote_tweets(tweet_id)  # getting al quote tweets

            print("Calling retweet api")
            d = self.get_all_retweets(tweet_id)  # getting all retweets

        else:
            print("No of Quote Tweets: ", 0)
            print("No of Retweets: ", 0)
            G = nx.DiGraph()
            G.add_node(uid)
            return G, self.nodes  # getting all retweets
        print("No of Quote Tweets: ", len(q))
        print("No of Retweets: ", len(d))
        if len(d) == 0 and len(q) == 0:  # it no retweets or quote tweets are available
            G = nx.DiGraph()
            G.add_node(uid)
            return G, self.nodes
        # getting the following of retweet users and dstore in dictionary
        if nodes != {} and nodes != None:
            self.nodes = nodes

        # print("Nodes :", self.nodes)
        # no need to find the following of root cascade node and also no need to find following of earliest tweet
        # self.nodes[uid] = []

        # getting count of followers and following  of all user to find out popular account
        follower_count, following_counts = self.get_follower_count(
            user_list=[uid] + [i.id for i in d]
        )

        # getting list of all following account of users
        for i in range(0, len(d) - 1):
            if d[i].id not in self.nodes:
                following_count = following_counts[
                    d[i].id
                ]  # getting the followng count form the dictionary
                if following_count > 1000:
                    print("Following more than 1000")
                    self.nodes[d[i].id] = [uid]
                elif following_count == 0:
                    self.nodes[d[i].id] = []
                elif following_count < 400:
                    f = []
                    self.get_following_manually(arr=f, user_name=d[i].username)
                    print("Following count for {} : {}".format(d[i].username, len(f)))
                    self.nodes[d[i].id] = f
                else:
                    limit = self.api.rate_limit_status()["resources"]["friends"][
                        "/friends/ids"
                    ]["remaining"]
                    if limit > 0:
                        f = self.get_all_following(d[i].id)
                        print(
                            "Following count for using api {} : {}".format(
                                d[i].username, len(f)
                            )
                        )
                        self.nodes[d[i].id] = f
                    else:
                        try:

                            f = self.get_all_following2(d[i].id)
                            print(
                                "Following count for using api 2 {} : {}".format(
                                    d[i].username, len(f)
                                )
                            )
                            self.nodes[d[i].id] = f
                        except Exception as e:
                            f = []
                            self.get_following_manually(arr=f, user_name=d[i].username)
                            print(
                                "Following count for using manually {} : {}".format(
                                    d[i].username, len(f)
                                )
                            )
                            self.nodes[d[i].id] = f

        # count= 0
        G = nx.DiGraph()
        G.add_nodes_from(
            [uid] + [i.id for i in d]
        )  # adding all the nodes to the graph retweets nodes + cascade node
        G.add_edge(uid, d[-1].id)  # adding edge between earliest and cascade node

        ordered_nodes = []
        ordered_nodes.append(uid)
        ordered_nodes.append(d[-1].id)
        for x in d[-2::-1]:  # reverse order
            # print(ordered_nodes)
            # no_common_followers=[] # list of ids that dont hv common followers so we will assign them under the most popular user
            id = self.get_latest_following(x.id, ordered_nodes, self.nodes)
            if id != -1:
                G.add_edge(id, x.id)
            else:
                curr_popular_follower_count = max(
                    [follower_count[i] for i in ordered_nodes]
                )  # get the most popular follower count based current nodes in the graph
                for z, y in follower_count.items():
                    if y == curr_popular_follower_count:
                        curr_popular = z  # get the most popular follower user id based current nodes in the graph
                # print(curr_popular,curr_popular_follower_count,x.id)

                G.add_edge(curr_popular, x.id)  # add the edge
                # no_common_followers.append(x.id)
            ordered_nodes.append(x.id)

        # getting graphs of quote tweets
        graphs = []
        for i in q:
            print("\nGetting quote tweet graph of :", i.id)
            G_quotes = self.get_graph_of_quotetweet(i.id)
            graphs.append(G_quotes)

        graphs.append(G)
        F = nx.compose_all(
            graphs
        )  # comnbine the rewteet graphs with individual quote graphs

        for i in range(len(u)):
            F.add_edge(uid, u[i].id)

        self.retweet_graph = G
        self.full_graph = F
        return F, self.nodes

    # compute a graph for quote tweets
    def get_graph_of_quotetweet(self, tweet_id):
        print("Getting Graph for Quote tweet :", tweet_id)
        uid = self.api.lookup_statuses([tweet_id])[
            0
        ].user.id  # getting user id of the person who tweeted the cascade node
        d = self.get_all_retweets(tweet_id)  # getting all retweets
        # print("No of Quote Tweets: ",len(q))
        print("No of Retweets: ", len(d))

        if len(d) == 0:  # it no retweets or quote tweets are available
            G = nx.DiGraph()
            G.add_node(uid)
            return G

        # getting count of followers and following  of all user to find out popular account
        follower_count, following_counts = self.get_follower_count(
            user_list=[uid] + [i.id for i in d]
        )

        # getting list of all following account of users
        # count = 0
        for i in range(0, len(d) - 1):
            if d[i].id not in self.nodes:

                following_count = following_counts[
                    d[i].id
                ]  # getting the followng count form the dictionary
                # print(following_count)
                if following_count == 0:
                    self.nodes[d[i].id] = [uid]
                if following_count < 2000:
                    f = []
                    self.get_following_manually(arr=f, user_name=d[i].username)
                    print("Following acount for {} : {}".format(d[i].username, len(f)))
                    self.nodes[d[i].id] = f
                else:
                    limit = self.api.rate_limit_status()["resources"]["friends"][
                        "/friends/ids"
                    ]["remaining"]
                    if limit > 0:  # we have api calls left
                        f = self.get_all_following(d[i].id)
                        print(
                            "Following acount for using api {} : {}".format(
                                d[i].username, len(f)
                            )
                        )
                        self.nodes[d[i].id] = f
                        count += 1
                    else:  # no more api calls left so have to manually scrape
                        f = []
                        self.get_following_manually(arr=f, user_name=d[i].username)
                        print(
                            "Following acount for {} : {}".format(d[i].username, len(f))
                        )
                        self.nodes[d[i].id] = f

        # count= 0
        G = nx.DiGraph()
        G.add_nodes_from(
            [uid] + [i.id for i in d]
        )  # adding all the nodes to the graph retweets nodes + cascade node
        G.add_edge(uid, d[-1].id)  # adding edge between earliest and cascade node

        ordered_nodes = []
        ordered_nodes.append(uid)
        ordered_nodes.append(d[-1].id)
        for x in d[-2::-1]:  # reverse order
            # print(ordered_nodes)
            # no_common_followers=[] # list of ids that dont hv common followers so we will assign them under the most popular user
            id = self.get_latest_following(x.id, ordered_nodes, self.nodes)
            if id != -1:
                G.add_edge(id, x.id)
            else:
                curr_popular_follower_count = max(
                    [follower_count[i] for i in ordered_nodes]
                )  # get the most popular follower count based current nodes in the graph
                for z, y in follower_count.items():
                    if y == curr_popular_follower_count:
                        curr_popular = z  # get the most popular follower user id based current nodes in the graph
                # print(curr_popular,curr_popular_follower_count,x.id)
                G.add_edge(curr_popular, x.id)  # add the edge
                # no_common_followers.append(x.id)
            ordered_nodes.append(x.id)

        return G

    # get list of all retweets tweets given a tweet ID
    def get_all_retweets(self, id):
        retweeters = []
        d = self.client.get_retweeters(id, max_results=100)
        if d.data == None:
            return []
        retweeters += d.data
        length = d.meta["result_count"]
        if "next_token" in d.meta:
            next_token = d.meta["next_token"]
            while True:
                # print(length)
                d = self.client.get_retweeters(
                    id, max_results=100, pagination_token=next_token
                )
                if d.data != None:
                    retweeters += d.data
                # length +=d.meta['result_count']
                if "next_token" not in d.meta:
                    break
                next_token = d.meta["next_token"]
        return retweeters

    # due to limit of Twitter API call (of 15 calls/15 min),
    # this function manually scrapes following from the user ID
    def get_following_manually(self, arr, user_name):
        import requests
        import json
        import time

        followers_file = open("followers.txt", "w+", encoding="utf-8")
        following_file = open("following.txt", "w+", encoding="utf-8")

        brief_dict = {}

        # Here Paste Your Twitter Cookie
        cookie = 'xxxxxxx'

        # Here Paste your Authoriaztion Token
        authorization = "xxxxxxx"

        # Here Paste your CSRF Token
        csrf_token = "xxxxxxx"

        # Check Documentation to find out how to get his values.

        # Extracts the Information from the API Repsonse  & Store it in followers.txt & following.txt
        def infoExtractor(JSONpayload, index, typeRequest, arr):
            if typeRequest == "followers_timeline":
                file = followers_file
            else:
                file = following_file
            if (
                JSONpayload["data"]["user"][typeRequest]["timeline"]["instructions"][
                    index
                ]["type"]
                == "TimelineAddEntries"
            ):
                userInfo = JSONpayload["data"]["user"][typeRequest]["timeline"][
                    "instructions"
                ][index]["entries"]
                # print(userInfo[3]["content"]["itemContent"]["user"]["rest_id"])

                for i in range(0, len(userInfo) - 2):
                    # brief_dict["screen_name"] = str(userInfo[i]["content"]["itemContent"]["user"]["legacy"]["screen_name"])
                    brief_dict["id"] = str(
                        userInfo[i]["content"]["itemContent"]["user"]["rest_id"]
                    )
                    arr.append(brief_dict["id"])
                    file.write(json.dumps(brief_dict) + "\n")
                return userInfo[len(userInfo) - 2]["content"]["value"]

            elif (
                JSONpayload["data"]["user"][typeRequest]["timeline"]["instructions"][
                    index
                ]["type"]
                == "TimelineTerminateTimeline"
            ):
                userInfo = JSONpayload["data"]["user"][typeRequest]["timeline"][
                    "instructions"
                ][index + 1]["entries"]

                for i in range(0, len(userInfo) - 2):
                    brief_dict["id"] = str(
                        userInfo[i]["content"]["itemContent"]["user"]["rest_id"]
                    )
                    arr.append(brief_dict["id"])
                    file.write(json.dumps(brief_dict) + "\n")

                return ""

        # Sends the API request to the Twitter Servers
        def runProgram(option, header_option, user_id, count, arr):
            headers = {
                "authority": "twitter.com",
                "authorization": authorization,
                "x-twitter-client-language": "en",
                "x-csrf-token": csrf_token,
                "x-twitter-auth-type": "OAuth2Session",
                "x-twitter-active-user": "yes",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36 Edg/89.0.774.45",
                "content-type": "application/json",
                "accept": "*/*",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://twitter.com/dlw_mlda/" + option,
                "accept-language": "en-US,en;q=0.9",
                "cookie": cookie,
            }

            if option == "followers":
                payload = requests.get(
                    "https://twitter.com/i/api/graphql/86vlEx-ifXptbl2JmLfxHg/Followers?variables=%7B%22userId%22%3A%22"
                    + user_id
                    + "%22%2C%22count%22%3A"
                    + count
                    + "%2C%22withHighlightedLabel%22%3Afalse%2C%22withTweetQuoteCount%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22withTweetResult%22%3Afalse%2C%22withUserResults%22%3Afalse%2C%22withNonLegacyCard%22%3Atrue%7D",
                    headers=headers,
                    timeout=2300,
                ).text
            else:
                payload = requests.get(
                    "https://twitter.com/i/api/graphql/taJbMVFxNBcULs8aHwX3cg/Following?variables=%7B%22userId%22%3A%22"
                    + user_id
                    + "%22%2C%22count%22%3A"
                    + count
                    + "%2C%22withHighlightedLabel%22%3Afalse%2C%22withTweetQuoteCount%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22withTweetResult%22%3Afalse%2C%22withUserResults%22%3Afalse%2C%22withNonLegacyCard%22%3Atrue%7D",
                    headers=headers,
                    timeout=2300,
                ).text

            firstCursor = infoExtractor(
                json.loads(payload), 2, header_option, arr
            ).split("|")

            while True:
                if option == "followers":
                    payload = requests.get(
                        "https://twitter.com/i/api/graphql/86vlEx-ifXptbl2JmLfxHg/Followers?variables=%7B%22userId%22%3A%22"
                        + user_id
                        + "%22%2C%22count%22%3A"
                        + count
                        + "%2C%22cursor%22%3A%22"
                        + firstCursor[0]
                        + "%7C"
                        + firstCursor[1]
                        + "%22%2C%22withHighlightedLabel%22%3Afalse%2C%22withTweetQuoteCount%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22withTweetResult%22%3Afalse%2C%22withUserResults%22%3Afalse%2C%22withNonLegacyCard%22%3Atrue%7D",
                        headers=headers,
                        timeout=2300,
                    ).text
                else:
                    payload = requests.get(
                        "https://twitter.com/i/api/graphql/taJbMVFxNBcULs8aHwX3cg/Following?variables=%7B%22userId%22%3A%22"
                        + user_id
                        + "%22%2C%22count%22%3A"
                        + count
                        + "%2C%22cursor%22%3A%22"
                        + firstCursor[0]
                        + "%7C"
                        + firstCursor[1]
                        + "%22%2C%22withHighlightedLabel%22%3Afalse%2C%22withTweetQuoteCount%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22withTweetResult%22%3Afalse%2C%22withUserResults%22%3Afalse%2C%22withNonLegacyCard%22%3Atrue%7D",
                        headers=headers,
                        timeout=2300,
                    ).text

                firstCursor = infoExtractor(json.loads(payload), 0, header_option, arr)
                if firstCursor == "":
                    break
                else:
                    firstCursor = firstCursor.split("|")

        if __name__ == "__main__":
            start = time.time()
            if (cookie == "" or authorization == "" or csrf_token == "") and 1 != 1:
                print(
                    "Pls Check the Cookie, Authorization & csrf token in the Code. Check the Documentation to know how ot get them!"
                )
            else:
                first_header = {
                    "authority": "twitter.com",
                    "authorization": authorization,
                    "x-twitter-client-language": "en",
                    "x-csrf-token": csrf_token,
                    "x-guest-token": "1371160710940561409",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 Edg/89.0.774.50",
                    "content-type": "application/json",
                    "accept-language": "en-US,en;q=0.9",
                    "cookie": cookie,
                }
                screen_name = user_name

                payload = requests.get(
                    "https://twitter.com/i/api/graphql/hc-pka9A7gyS3xODIafnrQ/UserByScreenName?variables=%7B%22screen_name%22%3A%22"
                    + screen_name
                    + "%22%2C%22withHighlightedLabel%22%3Atrue%7D",
                    headers=first_header,
                ).text

                try:
                    user_payload = json.loads(payload)
                    user_id = user_payload["data"]["user"]["rest_id"]
                    followers_count = user_payload["data"]["user"]["legacy"][
                        "followers_count"
                    ]
                    following_count = user_payload["data"]["user"]["legacy"][
                        "friends_count"
                    ]

                    if following_count > 12000:
                        following_count_limit = 12000 - 100
                    else:
                        following_count_limit = following_count - 4

                    following_count_limit = 1000
                    runProgram(
                        "following",
                        "following_timeline",
                        user_id,
                        str(following_count - 1),
                        arr,
                    )
                    end = time.time()
                    print(str(end - start) + " seconds spent.")

                except Exception as e:
                    print("Error: " + str(e))
                    # print("Pls Check the Username or all token, if still error, then post in the repo.")

    # get list of all quote tweets given a tweet ID
    def get_all_quote_tweets(self, id):
        quote_tweets = []
        users = []
        d = self.client.get_quote_tweets(
            id, max_results=100, user_fields=["id"], expansions="author_id"
        )
        if d.data == None:
            return [], []
        quote_tweets += d.data
        users += d.includes["users"]
        length = d.meta["result_count"]
        if "next_token" in d.meta:
            next_token = d.meta["next_token"]
            while True:
                # print(length)
                d = self.client.get_quote_tweets(
                    id,
                    max_results=100,
                    pagination_token=next_token,
                    user_fields=["id"],
                    expansions="author_id",
                )
                if d.data != None:
                    quote_tweets += d.data
                    users += d.includes["users"]
                # length +=d.meta['result_count']
                if "next_token" not in d.meta:
                    break
                next_token = d.meta["next_token"]

        return quote_tweets, users

    # get list of all following of a particular account using Twitter API v2
    def get_all_following2(self, uid):
        client = tweepy.Client(
            self.bearer_token,
            self.consumer_key,
            self.consumer_secret,
            self.access_token_key,
            self.access_token_secret,
            wait_on_rate_limit=False,
        )
        following = client.get_users_following(id=uid)
        return following

    # get list of all following of a particular account using Twitter API
    def get_all_following(self, uid):
        following = []
        for i in tweepy.Cursor(
            self.api.get_friend_ids, user_id=uid, count=5000
        ).pages():
            following += i

        return following

    # get list of all followers of a particular account using Twitter API
    def get_all_followers(self, uid):
        followers = []

        for i in tweepy.Cursor(self.api.get_follower, user_id=uid, count=5000).pages():
            followers += i

        return followers

    # get the count of followerCount and followingCount
    def get_follower_count(self, user_list):
        if len(user_list) > 100:
            data = []
            for i in range(100, len(user_list), 100):
                data += self.api.lookup_users(user_id=user_list[i - 100 : i])
            data += self.api.lookup_users(user_id=user_list[i:])

        else:
            data = self.api.lookup_users(user_id=user_list)

        count = {}
        count_2 = {}
        for i in data:
            count[i.id] = i.followers_count
            count_2[i.id] = i.friends_count
        return count, count_2

    # function to get the  latest following account For any account if 𝑣𝑖 retweets the same news later than
    # atleast one following accounts in {𝑣1, . . . , 𝑣𝑛}, we estimate the news
    # spreads from the account with the latest timestamp to account 𝑣
    # Since the latest tweets are first presented in the timeline of the
    # Twitter app, and thus have higher probabilities to be retweeted.
    def get_latest_following(self, id, ordered_nodes, nodes):
        for i in ordered_nodes[::-1]:
            if i in nodes[id]:
                return i
        return -1
