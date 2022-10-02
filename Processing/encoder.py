# For Twitter API
import json
from logging import exception
import tweepy
from tweepy import OAuthHandler
from datetime import datetime

# For Spacy 
import re
import torch
import numpy as np
import spacy
import en_core_web_lg

# For Reading adjlist using NetworkX
import networkx as nx

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('words')
from nltk.corpus import stopwords
from string import punctuation
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

from sklearn.feature_extraction.text import CountVectorizer

class Encoder:
  def __init__(self):
    # Pratham's API Keys (top secret)
    self.consumer_key = "xxxxxxx"
    self.consumer_secret = "xxxxxxx"
    self.access_token_key = "xxxxxxx"
    self.access_token_secret = "xxxxxxx"
    self.bearer_token = "xxxxxxx"
    auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
    auth.set_access_token(self.access_token_key, self.access_token_secret)
    self.api = tweepy.API(auth, wait_on_rate_limit=True)
    self.nlp = en_core_web_lg.load()

  def getUserTimeLine(self, userID):
    response = []
    texts=[]
    try:

      response = self.api.user_timeline(user_id=userID, count=200)

    except Exception as err:
      if str(err) == 'Not authorized.':
        print(str(err))
        print(f'Not authorized.')
      else:
        print(str(err))
        print(f'Page does not exist')

    for i in range(len(response)):
      texts.append(re.sub(r"http\S+", "", response[i]._json["text"])) # Also remove URLs

    return texts


  def profileEncoder(self, listOfUserIDs):
    """
      Code to generate 10-dimensional user profile feature based on crawled user object using Twitter Developer API
    """
    try:
        if(len(listOfUserIDs)>100):
          response=[]

          for i in range(100,len(listOfUserIDs),100):
            response += self.api.lookup_users(user_id=listOfUserIDs[i-100:i])
          response += self.api.lookup_users(user_id=listOfUserIDs[i:])
        else:
          response = self.api.lookup_users(user_id=listOfUserIDs)

    except Exception as err:  # handle deleted/suspended accounts
        if str(err) == 'Not authorized.':
            print(f'Not authorized ')
        else:
            print(f'Page does not exist')

    user_dict = {}
    for i in range(len(response)):
        user_dict[response[i]._json.get('id')] = response[i]._json
    
    feature = np.zeros([len(user_dict), 10], dtype=np.float32)
    id_counter = 0
    est_date = datetime.fromisoformat('2006-03-21')
    for profile in user_dict.values():
        # 1) Verified?, 2) Enable geo-spatial positioning, 3) Followers count, 4) Friends count
        vector = [int(profile['verified']), int(profile['geo_enabled']), profile['followers_count'],
                  profile['friends_count']]
        # 5) Status count, 6) Favorite count, 7) Number of lists
        vector += [profile['statuses_count'], profile['favourites_count'], profile['listed_count']]

        # 8) Created time (No. of months since Twitter established)
        user_date = datetime.strptime(profile['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        month_diff = (user_date.year - est_date.year) * 12 + user_date.month - est_date.month
        vector += [month_diff]

        # 9) Number of words in the description, 10) Number of words in the screen name
        vector += [len(profile['name'].split()), len(profile['description'].split())]

        feature[id_counter, :] = np.reshape(vector, (1, 10))
        id_counter += 1

    return feature

  def clean_text(self, text):
    # lower text
    text = text.lower()
    # tokenize text and remove puncutation
    text = [word.strip(punctuation) for word in text.split(" ")]
    # remove words that contain numbers
    text = [word for word in text if not any(c.isdigit() for c in word)]
    # remove stop words
    stop = set(stopwords.words('english'))
    text = set(text)
    text = [x for x in text if x not in stop]
    # remove empty tokens
    text = [t for t in text if len(t) > 0]
    # pos tag text
    text = " ".join(text)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
    print(emoji_pattern.sub(r'', text)) # no emoji
    print(text)
    return text

  
  def historyEncoder(self, arrayOfTexts:np.array):

    # basic cleaning
    for i in range(len(arrayOfTexts)):
      arrayOfTexts[i] = self.clean_text(arrayOfTexts[i])

    # generating the vocabulary
    print("Histroy encode of array of text shape ",arrayOfTexts.shape)
    Vectorizer = CountVectorizer()
    x = Vectorizer.fit_transform(arrayOfTexts)
    vocab = Vectorizer.get_feature_names_out()

    # print(vocab)
    # generate the embedding matrix
    num_tokens = len(vocab)
    embedding_dim = len(self.nlp('The').vector)
    embedding_matrix_all = np.zeros((num_tokens, embedding_dim))
    for i, word in enumerate(vocab):
      embedding_matrix_all[i] = self.nlp(str(word)).vector

    # we average the embedding vectors of the words in the 200 tweets
    embedded_array = np.zeros(300)
    for i in range(len(embedding_matrix_all)):
      embedded_array = embedded_array + embedding_matrix_all[i]
    embedded_array = embedded_array / num_tokens

    return embedded_array


  def getInputToModel(self, graph, article):
    # graph - networkx graph object
    #G = nx.read_adjlist(pathToAdjList)
    G = graph

    # article - dict (json response) [used for encoding the root node]
    rootText = article['title'] + article['text']  

    # Initialize some lists
    userIds = [str(node) for node in G.nodes if node > 0] # filter out the root (dummy node)
    spacy = np.zeros(shape=(len(userIds)+1, 300))

    # Encode the root node
    print("Enocoding Root Text")
    rootText = np.array([rootText])
    rootVector = self.historyEncoder(rootText)
    spacy[0] = rootVector
    print("Enocoding Root Text done")

    for i in range(len(userIds)): 
      userId = userIds[i]
      print("Getting user timeline of ",userId)
      texts = self.getUserTimeLine(userId)
      print("Length of tweets available of the user ",len(texts))

      # Encode the texts
      texts = np.array(texts)
      historyVector = self.historyEncoder(texts)
      print(historyVector.shape)
      # Collect the Encodings
      spacy[i+1] = historyVector
    
    # Get the profile Encoding (note this works on a list of user ids)
    profile = self.profileEncoder(userIds)

    # Pad the profile vector for the root node
    rootProfile = np.zeros(shape=(1, 10))
    profile = np.concatenate((rootProfile, profile), axis = 0)
    
    # Append the profile encodings to the history encodings
    content = np.concatenate((spacy, profile), axis=1)

    # Sanity Checks
    # print(spacy.shape)
    # print(profile.shape)
    # print(content.shape)

    # Convert the 2-D numpy array to a torch tensor
    inputToGNN = torch.tensor(content)
    return inputToGNN