import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import re
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM, Bidirectional, Embedding, Dropout
import tensorflow as tf
import os
from databaseController import (check_if_need_reload_model, update_need_reload_model,
update_need_reload_model_for_user, get_error_threshold, check_if_need_reload_error_threshold,
update_need_reload_error_threshold, update_need_reload_error_threshold_for_user)
from flask import session
import json

nltk.download("stopwords")
nltk.download('punkt')

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, 'model')
DATA_FILE = 'taggedData.json'

def cleaning(sentences):
  words = []
  for s in sentences:
    clean = re.sub(r'[^ a-z A-Z 0-9]', " ", s)
    w = word_tokenize(clean)
    #stemming
    words.append([i.lower() for i in w])

  return words

def get_sentences(intents):
  sentences = []
  for intent in intents['intents']:
    for sentence in intent['patterns']:
      sentences.append(sentence)
  return sentences

def create_tokenizer(words, filters = '!"#$%&()*+,-./:;<=>?@[\]^_`{|}~'):
  token = Tokenizer(filters = filters)
  token.fit_on_texts(words)
  return token

def max_length(words):
  return(len(max(words, key = len)))

def encoding_doc(token, words):
  return(token.texts_to_sequences(words))

def padding_doc(encoded_doc, max_length):
  return(pad_sequences(encoded_doc, maxlen = max_length, padding = "post"))

def get_intents(intents):
  tags = []
  for intent in intents['intents']:
    tags.append(intent['tag'])
  return tags

def create_model(vocab_size, max_length, num_tags):
  model = Sequential()
  model.add(Embedding(vocab_size, 128, input_length = max_length, trainable = False))
  model.add(Bidirectional(LSTM(128)))
    #   model.add(LSTM(128))
  model.add(Dense(32, activation = "relu"))
  model.add(Dropout(0.5))
  model.add(Dense(num_tags, activation = "softmax"))

  return model

graph_1 = tf.compat.v1.Graph()
k_session_1 = tf.compat.v1.Session(graph=graph_1)

def load_trained_model():
    with open(DATA_DIR + '/' + DATA_FILE) as json_data:
        intents = json.load(json_data)

    sentences = get_sentences(intents)
    cleaned_words = cleaning(sentences)
    word_tokenizer = create_tokenizer(cleaned_words)
    vocab_size = len(word_tokenizer.word_index) + 1
    max_len = max_length(cleaned_words)
    encoded_doc = encoding_doc(word_tokenizer, cleaned_words)
    padded_doc = padding_doc(encoded_doc, max_len)
    unique_intents = get_intents(intents)
    num_tags = len(unique_intents)

    with graph_1.as_default():
        with k_session_1.as_default():
          model = create_model(vocab_size, max_len, num_tags)
          model.compile(loss = "categorical_crossentropy", optimizer = "adam", metrics = ["accuracy"])
          model.summary()
          model = load_model(DATA_DIR + "/keras_intent_classifier/model.h5")
          model._make_predict_function()

    return word_tokenizer, unique_intents, max_len, model

def predictions(text):
  clean = re.sub(r'[^ a-z A-Z 0-9]', " ", text)
  test_word = word_tokenize(clean)
  test_word = [w.lower() for w in test_word]
  test_ls = word_tokenizer.texts_to_sequences(test_word)

  #Check for unknown words
  if [] in test_ls:
    test_ls = list(filter(None, test_ls))

  test_ls = np.array(test_ls).reshape(1, len(test_ls))

  x = padding_doc(test_ls, max_len)

  with graph_1.as_default():
        with k_session_1.as_default():
          pred = model.predict(x)

  return pred

def get_final_output(pred, classes):
  predictions = pred[0]

  classes = np.array(classes)
  ids = np.argsort(-predictions)
  classes = classes[ids]
  predictions = -np.sort(-predictions)

  return (classes, predictions)

ERROR_THRESHOLD = get_error_threshold()
word_tokenizer, unique_intents, max_len, model = load_trained_model()

def classify_intent(text, userID):
  global word_tokenizer
  global unique_intents
  global max_len
  global model
  global ERROR_THRESHOLD

  need_reload_model = check_if_need_reload_model(userID)
  if need_reload_model:
      word_tokenizer, unique_intents, max_len, model = load_trained_model()
      update_need_reload_model_for_user(False, userID)

  need_reload_error_threshold = check_if_need_reload_error_threshold(userID)
  if need_reload_error_threshold:
      ERROR_THRESHOLD = get_error_threshold()
      update_need_reload_error_threshold_for_user(False, userID)

  try:
      pred = predictions(text)
      classes, preds = get_final_output(pred, unique_intents)
      # filter out predictions below a threshold
      results = [[i,r] for i,r in enumerate(preds) if r>ERROR_THRESHOLD]
      # sort by strength of probability
      results.sort(key=lambda x: x[1], reverse=True)
      return_list = []
      for r in results:
          return_list.append((classes[r[0]], r[1]))
      # return tuple of intent and probability
      return return_list
  except:
      return_list = []
      return return_list
