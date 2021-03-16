import numpy as np
import os
import pandas as pd
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflow as tf
import random
from databaseController import check_if_need_reload_sentiment_analyser, update_need_reload_sentiment_analyser_for_user

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, 'model')

POS_THRESHOLD = 0.9
NEG_THRESHOLD = 0.05
INPUT_LENGTH = 60

EMOJI_RESPONSE_POS = [ '😀', '😄', '😁', '😊']
EMOJI_RESPONSE_NEG = [ '😢', '😔', '😧', '☹️', '😞', '🙁']

graph_2 = tf.compat.v1.Graph()
k_session_2 = tf.compat.v1.Session(graph=graph_2)

def load_trained_sentiment_model():
    tweet_dataset = pd.read_csv(DATA_DIR + '/processed_tweets.csv')
    X_data = np.array(tweet_dataset['processed_text'])
    tokenizer = Tokenizer(filters="", lower=False, oov_token="<oov>")
    tokenizer.fit_on_texts(X_data)

    with graph_2.as_default():
        with k_session_2.as_default():
            sentiment_model = tf.keras.models.load_model(DATA_DIR + '/Twitter-Sentiment-BiLSTM')

    return tokenizer, sentiment_model

tokenizer, sentiment_model = load_trained_sentiment_model()

def classify_sentiment(sentence, userID):
    global tokenizer
    global sentiment_model

    need_reload_sentiment_analyser = check_if_need_reload_sentiment_analyser(userID)

    if need_reload_sentiment_analyser:
        tokenizer, sentiment_model = load_trained_sentiment_model()
        update_need_reload_sentiment_analyser_for_user(False, userID)

    input_list = list()
    input_list.append(sentence)
    sequences = tokenizer.texts_to_sequences(input_list)
    padded = pad_sequences(sequences, maxlen=INPUT_LENGTH)
    with graph_2.as_default():
        with k_session_2.as_default():
            classes = sentiment_model.predict(padded)
            if (classes[0][0] > POS_THRESHOLD):
                return random.choice(EMOJI_RESPONSE_POS)
            elif (classes[0][0] < NEG_THRESHOLD):
                return random.choice(EMOJI_RESPONSE_NEG)
            else:
                return ''
