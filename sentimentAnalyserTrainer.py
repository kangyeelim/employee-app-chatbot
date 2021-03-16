import tensorflow as tf
import numpy as np
import pandas as pd
import re
import csv
from tempfile import NamedTemporaryFile
import shutil
import os

from gensim.models import Word2Vec
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Bidirectional, GlobalMaxPool1D, Dense, LSTM, Conv1D, Embedding
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping
from keras.backend import clear_session

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, 'model')

contractions = pd.read_csv(DATA_DIR + '/contractions.csv', index_col='Contraction')
contractions.index = contractions.index.str.lower()
contractions.Meaning = contractions.Meaning.str.lower()
contractions_dict = contractions.to_dict()['Meaning']

graph = tf.compat.v1.Graph()
k_session = tf.compat.v1.Session(graph=graph)

# Defining regex patterns.
urlPattern        = r"((http://)[^ ]*|(https://)[^ ]*|(www\.)[^ ]*)"
userPattern       = '@[^\s]+'
hashtagPattern    = '#[^\s]+'
alphaPattern      = "[^a-z0-9<>]"
sequencePattern   = r"(.)\1\1+"
seqReplacePattern = r"\1\1"

# Defining regex for emojis
smileemoji        = r"[8:=;]['`\-]?[)d]+"
sademoji          = r"[8:=;]['`\-]?\(+"
neutralemoji      = r"[8:=;]['`\-]?[\/|l*]"
lolemoji          = r"[8:=;]['`\-]?p+"

def preprocess_apply(tweet):

    tweet = tweet.lower()

    # Replace all URls with '<url>'
    tweet = re.sub(urlPattern,'<url>',tweet)
    # Replace @USERNAME to '<user>'.
    tweet = re.sub(userPattern,'<user>', tweet)

    # Replace 3 or more consecutive letters by 2 letter.
    tweet = re.sub(sequencePattern, seqReplacePattern, tweet)

    # Replace all emojis.
    tweet = re.sub(r'<3', '<heart>', tweet)
    tweet = re.sub(smileemoji, '<smile>', tweet)
    tweet = re.sub(sademoji, '<sadface>', tweet)
    tweet = re.sub(neutralemoji, '<neutralface>', tweet)
    tweet = re.sub(lolemoji, '<lolface>', tweet)

    for contraction, replacement in contractions_dict.items():
        tweet = tweet.replace(contraction, replacement)

    # Remove non-alphanumeric and symbols
    tweet = re.sub(alphaPattern, ' ', tweet)

    # Adding space on either side of '/' to seperate words (After replacing URLS).
    tweet = re.sub(r'/', ' / ', tweet)
    return tweet

def getSentimentAnalysisModel(vocab_length, Embedding_dimensions, embedding_matrix, input_length):
    #tf.compat.v1.reset_default_graph()
    embedding_layer = Embedding(input_dim = vocab_length,
                                output_dim = Embedding_dimensions,
                                weights=[embedding_matrix],
                                input_length=input_length,
                                trainable=False)

    model = Sequential([
            embedding_layer,
            Bidirectional(LSTM(100, dropout=0.3, return_sequences=True)),
            Bidirectional(LSTM(100, dropout=0.3, return_sequences=True)),
            Conv1D(100, 5, activation='relu'),
            GlobalMaxPool1D(),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid'),
            ],
        name="Sentiment_Model")
    return model

import sys
DATASET_COLUMNS  = ["sentiment", "processed_text"]
def train_sentiment_model():
    dataset = pd.read_csv(DATA_DIR + '/processed_tweets.csv' , encoding = 'ISO-8859-1',  names=DATASET_COLUMNS)
    dataset = dataset.iloc[1:]
    print(dataset.head(), file=sys.stderr)
    
    X_data, y_data = np.array(dataset['processed_text']), np.array(dataset['sentiment'])

    X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size = 0.05, random_state = 0)

    Embedding_dimensions = 100

    # Creating Word2Vec training dataset.
    Word2vec_train_data = list(map(lambda x: x.split(), X_train))
    # Defining the model and training it.
    word2vec_model = Word2Vec(Word2vec_train_data,
                 size=Embedding_dimensions,
                 workers=8,
                 min_count=5)
    # Defining the model input length.
    input_length = 60

    tokenizer = Tokenizer(filters="", lower=False, oov_token="<oov>")
    tokenizer.fit_on_texts(X_data)

    vocab_length = len(tokenizer.word_index) + 1
    X_train = pad_sequences(tokenizer.texts_to_sequences(X_train), maxlen=input_length)
    X_test  = pad_sequences(tokenizer.texts_to_sequences(X_test) , maxlen=input_length)
    embedding_matrix = np.zeros((vocab_length, Embedding_dimensions))

    for word, token in tokenizer.word_index.items():
        if word2vec_model.wv.__contains__(word):
            embedding_matrix[token] = word2vec_model.wv.__getitem__(word)

    with graph.as_default():
        with k_session.as_default():
            training_model = getSentimentAnalysisModel(vocab_length, Embedding_dimensions, embedding_matrix, input_length)
            training_model.summary()
            callbacks = [ReduceLROnPlateau(monitor='val_loss', patience=5, cooldown=0),
                EarlyStopping(monitor='val_accuracy', min_delta=1e-4, patience=5)]
            training_model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
            history = training_model.fit(
                X_train, y_train,
                batch_size=1024,
                epochs=12,
                validation_split=0.1,
                callbacks=callbacks,
                verbose=1,
            )
            # Saving the TF-Model.
            training_model.save(DATA_DIR + '/sentiment/Twitter-Sentiment-BiLSTM')

def add_tagged_data_in_csv_training_file(input_list):
    processed_list = []
    for input in input_list:
        processed_text = preprocess_apply(input[1])
        processed_list.append((input[0], processed_text))

    tempfile = NamedTemporaryFile('w+t', newline='', delete=False)
    tmp_csv_f = csv.writer(tempfile)
    tempfile_name = tempfile.name
    count = -1
    with open(DATA_DIR + '/processed_tweets.csv') as f:
        csv_f = csv.reader(f)

        is_header = True
        for row in csv_f:
            if is_header:
                tmp_csv_f.writerow(row)
                is_header = False
            elif not is_header and not row[2] in (input[1] for input in processed_list):
                count = count + 1
                tmp_csv_f.writerow([count, row[1], row[2]])


    for input in processed_list:
        if input[0] == 1 or input[0] == 0:
            count = count + 1
            tmp_csv_f.writerow([count, input[0], input[1]])

    tempfile.close()
    shutil.move(tempfile_name, DATA_DIR + '/processed_tweets.csv')
