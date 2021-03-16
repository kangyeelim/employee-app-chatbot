import numpy as np
from sklearn.preprocessing import OneHotEncoder
from keras.callbacks import ModelCheckpoint
from keras.backend import clear_session
from intentClassifier import get_intents, get_sentences, cleaning, create_tokenizer, encoding_doc, padding_doc, create_model
import os
from sklearn.model_selection import train_test_split
import json

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, 'model')
DATA_FILE = 'taggedData.json'

def max_length(words):
  return(len(max(words, key = len)))

def form_intent_list_to_patterns(intents):
  intent_list = []
  for intent in intents['intents']:
    tag = intent['tag']
    for pattern in intent['patterns']:
      intent_list.append(tag)
  return intent_list

def one_hot(encode):
  o = OneHotEncoder(sparse = False)
  return(o.fit_transform(encode))

def train_data():

    # import our chat-bot intents file
    with open(DATA_DIR + '/' + DATA_FILE) as json_data:
        intents = json.load(json_data)

    unique_intents = get_intents(intents)
    sentences = get_sentences(intents)
    cleaned_words = cleaning(sentences)

    word_tokenizer = create_tokenizer(cleaned_words)
    vocab_size = len(word_tokenizer.word_index) + 1

    encoded_doc = encoding_doc(word_tokenizer, cleaned_words)

    max_len = max_length(cleaned_words)
    padded_doc = padding_doc(encoded_doc, max_len)

    #tokenizer with filter changed
    output_tokenizer = create_tokenizer(unique_intents, filters = '!"#$%&()*+,-/:;<=>?@[\]^`{|}~')
    num_tags = len(unique_intents)

    intent_list_to_patterns = form_intent_list_to_patterns(intents)
    encoded_output = encoding_doc(output_tokenizer, intent_list_to_patterns)
    encoded_output = np.array(encoded_output).reshape(len(encoded_output), 1)

    output_one_hot = one_hot(encoded_output)

    train_X, val_X, train_Y, val_Y = train_test_split(padded_doc, output_one_hot, shuffle = True, test_size = 0.2)

    clear_session()

    model = create_model(vocab_size, max_len, num_tags)

    model.compile(loss = "categorical_crossentropy", optimizer = "adam", metrics = ["accuracy"])
    model.summary()

    filename = DATA_DIR + '/keras_intent_classifier/model.h5'
    checkpoint = ModelCheckpoint(filename, monitor='val_loss', verbose=1, save_best_only=True, mode='min')

    hist = model.fit(train_X, train_Y, epochs = 120, batch_size = 32, validation_data = (val_X, val_Y), callbacks = [checkpoint])

#update json file if a tag's name is edited
def edit_tag_in_json_training_file(oldTag, newTag):
    with open(DATA_DIR + '/' + DATA_FILE) as json_data:
        intents = json.load(json_data)
    for intent in intents['intents']:
        if intent['tag'] == oldTag:

            intent['tag'] = newTag
    with open(DATA_DIR + '/' + DATA_FILE, 'w') as fp:
        json.dump(intents, fp, indent=2)

#delete tag and its patterns if its deleted
def delete_tag_from_json_training_file(delTag):
    isExistingTag = False
    with open(DATA_DIR + '/' + DATA_FILE) as json_data:
        intents = json.load(json_data)
    for intent in intents['intents']:
        if intent['tag'] == delTag:
            intents['intents'].remove(intent)
            isExistingTag = True
    with open(DATA_DIR + '/' + DATA_FILE, 'w') as fp:
        json.dump(intents, fp, indent=2)
    return isExistingTag

#using all inputs in database, update json file
def add_tagged_data_in_json_training_file():
    with open(DATA_DIR + '/' + DATA_FILE) as json_data:
        intents = json.load(json_data)
    inputs = get_all_inputs()
    isExistingTag = False
    for input in list(inputs):
        #iterate through list of intents
        for intent in intents['intents']:
            #check if intent tag exist in json
            #append to patterns if exist
            #if do not allow repeating patterns, add: and not input['input'] in intent['patterns'] :
            if input['tag'] == intent['tag']:
                intent['patterns'].append(input['input'])
                isExistingTag = True

            #if the tag to an input is changed to not be tagged to that tag, remove from patterns
            if input['input'] in intent['patterns'] and not input['tag'] == intent['tag']:
                intent['patterns'] = list(filter(lambda x: x != input['input'], intent['patterns']))

        # if intent tag does not exist in json, create new entry for it
        if not isExistingTag and not tag == 'smalltalk.dialogpt' and not input['tag'] == 'sentiment.emoji' and not tag == 'context':
            entry = {
                "tag": input["tag"],
                "patterns": input['input']
            }
            intents['intents'].append(entry)

    with open(DATA_DIR + '/' + DATA_FILE, 'w') as fp:
        json.dump(intents, fp, indent=2)
    return isExistingTag

def add_tagged_data_in_json_training_file(tag, text):
    with open(DATA_DIR + '/' + DATA_FILE) as json_data:
        intents = json.load(json_data)
    isExistingTag = False
    #iterate through list of intents
    for intent in intents['intents']:
        #check if intent tag exist in json
        #append to patterns if exist
        #if do not allow repeating patterns, add: and not input['input'] in intent['patterns']:
        if tag == intent['tag']:
            intent['patterns'].append(text)
            isExistingTag = True

        #if the tag to an input is changed to not be tagged to that tag, remove from patterns
        if text in intent['patterns'] and not tag == intent['tag']:
            intent['patterns'] = list(filter(lambda x: x != text, intent['patterns']))

        # if intent tag does not exist in json, create new entry for it
    if not isExistingTag and not tag == 'smalltalk.dialogpt' and not tag == 'sentiment.emoji':
        entry = {
            "tag": tag,
            "patterns": text
        }
        intents['intents'].append(entry)

    with open(DATA_DIR + '/' + DATA_FILE, 'w') as fp:
        json.dump(intents, fp, indent=2)

    return isExistingTag
