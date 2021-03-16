import os
import json
import sys
from intentClassifier import classify_intent
from sentimentAnalyser import classify_sentiment, EMOJI_RESPONSE_POS, EMOJI_RESPONSE_NEG
from smallTalkGenerator import getSmallTalkResponse
from databaseController import *

# things we need for Tensorflow
import random
import re
from autocorrect import Speller


SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, 'model')

# methods to retrieve entities
def get_time_if_exist(input):
  time = ''
  containsTime = False
  sentence = input.lower()
  if re.findall(r"\d+[.]\d+\s*am", sentence):
    time = re.findall(r"\d+[.]\d+\s*am", sentence)[0]
    containsTime = True
  elif re.findall(r"\d+[:]\d+\s*am", sentence):
    time = re.findall(r"\d+[:]\d+\s*am", sentence)[0]
    containsTime = True
  elif re.findall(r"\d+\s*am", sentence):
    time = re.findall(r"\d+\s*am", sentence)[0]
    containsTime = True
  elif re.findall(r"\d+[.]\d+\s*pm", sentence):
    time = re.findall(r"\d+[.]\d+\s*pm", sentence)[0]
    containsTime = True
  elif re.findall(r"\d+[:]\d+\s*pm", sentence):
    time = re.findall(r"\d+[:]\d+\s*pm", sentence)[0]
    containsTime = True
  elif re.findall(r"\d+\s*pm", sentence):
    time = re.findall(r"\d+\s*pm", sentence)[0]
    containsTime = True
  return (containsTime, time)

MONTHS = ["jan", "january", "feb", "febuary", "mar", "march", "apr", "april", "may", "jun", "june", "jul", "july", "aug", "august", "sep", "september", "oct", "october", "nov", "november", "dec", "december"]
YEARS = ['21', '2021', '22', '2022']
DAYS = [("first", 1) , ("one", 1), ("second", 2), ("two", 2), ("third", 3), ("three", 3), ("forth", 4), ("four", 4), ("fifth", 5), ("five", 5), ("sixth", 6), ("six", 6), ("seventh", 7), ("seven", 7), ("eighth", 8), ("eigth", 8), ("ninth", 9), ("nine", 9), ("tenth", 10), ("ten", 10), ("eleventh", 11), ("eleven", 11), ("twelveth", 12), ("twelve", 12), ("thirteenth", 13), ("thirteen", 13), ("fourteenth", 14), ("fourteen", 14), ("fifthteen", 15), ("fifteen", 15),
        ("sixteenth", 16), ("sixteen", 16), ("seventeenth", 17), ("seventeen", 17), ("eighteenth", 18), ("eighteen", 18), ("nineteenth", 19), ("nineteen", 19), ("twentieth", 20), ("twenty", 20), ("twenty-first", 21), ("twenty first", 21), ("twenty-one", 21), ("twenty one", 21), ("twenty-second", 22), ("twenty second", 22), ("twenty-two", 22), ("twenty two", 22), ("twenty-third", 23), ("twenty third", 23),
        ("twenty-fourth", 24), ("twenty fourth", 24), ("twenty-fifth", 25), ("twenty fifth", 25), ("twenty-sixth", 26), ("twenty sixth", 26), ("twenty-seventh", 27), ("twenty seventh", 27), ("twenty-eighth", 28), ("twenty eighth", 28), ("twenty-eight", 28), ("twenty eight", 28),
        ("twenty-nineth", 29), ("twenty nineth", 29), ("twenty-nine", 29), ("twenty nine", 29), ("thirtieth", 30), ("thirty", 30), ("thirty-first", 31), ("thirty-one", 31), ("thirty one", 31), ("thrity first", 31)]

def get_date_if_exist(input):
  date = ''
  containsDate = False
  sentence = input.lower()
  if re.findall(r"today", sentence):
    date = "today"
    containsDate = True
  if re.findall(r"tmr", sentence) or re.findall(r"tomorrow", sentence):
    date = "tomorrow"
    containsDate = True
  if re.findall(r"\d+[-]\d+[-]\d+", sentence):
    date = re.findall(r"\d+[-]\d+[-]\d+", sentence)[0]
    containsDate = True
  if re.findall(r"\d+[/]\d+[/]\d+", sentence):
    date = re.findall(r"\d+[/]\d+[/]\d+", sentence)[0]
    containsDate = True
  if any(word in sentence for word in MONTHS):
    month_formats = [month for month in MONTHS if month in sentence]
    if any(word in sentence for word in YEARS):
      year_formats = [year for year in YEARS if year in sentence]
      if year_formats:
        for month in month_formats:
          for year in year_formats:
            res = re.findall(rf'\d+\s*{month}\s*{year}', sentence)
            if res:
              containsDate = True
              date = res[0]
        for month in month_formats:
            for year in year_formats:
              if any(day for day in DAYS if day[0] in sentence):
                day = (list(day for day in DAYS if day[0] in sentence))[-1][1]
                date = str(day) + " " + month + " " + year
                containsDate = True

      else:
        for month in month_formats:
          res = re.findall(rf'\d+\s*{month}', sentence)
          if res:
            containsDate = True
            date = res[0]
        for month in month_formats:
          if any(day for day in DAYS if day[0] in sentence):
            day = (list(day for day in DAYS if day[0] in sentence))[-1][1]
            containsDate = True
            date = str(day) + " " + month
  return (containsDate, date)

def get_unit_number_if_exist(input):
  unit = ''
  containsUnit = False
  sentence = input
  if re.findall(r"[#]\d+[-]\d+", sentence):
    unit = re.findall(r"[#]\d+[-]\d+", sentence)[0]
    containsUnit = True
  return (containsUnit, unit)

def get_duration_if_exist(input):
  duration = ''
  containsDur = False
  sentence = input.lower()
  if re.findall(r"\d+\s*[.]\s*\d+\s*hr[s]?", sentence):
    duration = re.findall(r"\d+\s*[.]\s*\d+\s*hr", sentence)[0].strip()
    containsDur = True
  elif re.findall(r"\d+\s*hr[s]?", sentence):
    duration = re.findall(r"\d+\s*hr", sentence)[0].strip()
    containsDur = True
  elif re.findall(r"\d*\s*[.]*\s*\d+\s*hour[s]?", sentence):
    duration = re.findall(r"\d*\s*[.]*\s*\d+\s*hour[s]?", sentence)[0].strip()
    containsDur = True
  elif re.findall(r"\d+\s*hour[s]?", sentence):
    duration = re.findall(r"\d+\s*hour[s]?", sentence)[0].strip()
    containsDur = True
  elif re.findall(r"\d+\s*min[s]?", sentence):
    duration = re.findall(r"\d+\s*min[s]?", sentence)[0].strip()
    containsDur = True
  elif re.findall(r"\d+\s*minutes", sentence):
    duration = re.findall(r"\d+\s*minutes", sentence)[0].strip()
    containsDur = True
  return (containsDur, duration)

BUILDINGS = ['annex', 'tower b', 'central manpower base', 'cmb']

def get_location_if_exist(input):
  sentence = input.lower()
  location = [i for i in BUILDINGS if i in sentence]
  containsLocation = len(location) > 0
  if len(location) > 0:
    res = location[0].capitalize()
  else:
    res = ''
  return (containsLocation, res)

# custom response based on entities
def book_meeting_room_task(input, data_dict, has_default_response=False):
  time_tuple = get_time_if_exist(input)
  date_tuple = get_date_if_exist(input)
  unit_tuple = get_unit_number_if_exist(input)
  dur_tuple = get_duration_if_exist(input)
  loc_tuple = get_location_if_exist(input)
  is_all_data_available = False
  response = ''
  if time_tuple[0]:
    data_dict['time'] = time_tuple[1]
  if date_tuple[0]:
    data_dict['date'] = date_tuple[1]
  if unit_tuple[0]:
    data_dict['unit'] = unit_tuple[1]
  if dur_tuple[0]:
    data_dict['duration'] = dur_tuple[1]
  if loc_tuple[0]:
    data_dict['location'] = loc_tuple[1]

  missing_data = []
  if ('time' in data_dict and 'date' in data_dict and 'unit' in data_dict and 'duration' in data_dict and 'location' in data_dict):
    is_all_data_available = True
    response = "Confirm to book meeting room at " + data_dict['location'] + " " + data_dict['unit'] + " for " + data_dict['date'] + " at " + data_dict['time'] + " for " + data_dict['duration'] + " ?"

  if not has_default_response:
    if (not 'time' in data_dict):
      missing_data.append('time')
    if (not 'date' in data_dict):
      missing_data.append('date')
    if (not 'location' in data_dict):
      missing_data.append('building')
    if (not 'unit' in data_dict):
      missing_data.append('meeting room unit number')
    if (not 'duration' in data_dict):
      missing_data.append('duration')
    if not is_all_data_available:
      if len(missing_data) == 1:
        response = 'How about the ' + missing_data[0] + '?'
      else:
        response = 'How about the'
        for data in missing_data[:-1]:
          response += (" " + data + ",")
        response += (" and " + missing_data[-1] + "?")

  return (is_all_data_available, data_dict, response)

def book_concierge_time_task(input, data_dict, has_default_response=False):
  time_tuple = get_time_if_exist(input)
  date_tuple = get_date_if_exist(input)
  response = ''
  is_all_data_available = False
  if time_tuple[0]:
    data_dict['time'] = time_tuple[1]
  if date_tuple[0]:
    data_dict['date'] = date_tuple[1]
  if ('time' in data_dict and 'date' in data_dict):
    is_all_data_available = True
    response = "Confirm to book time slot for concierge for " + data_dict['date'] + " at " + data_dict['time'] + " ?"
  if not has_default_response:
    if ('time' in data_dict and not 'date' in data_dict):
      response = ("How about the date?")
    elif (not 'time' in data_dict and 'date' in data_dict):
      response = ("How about the time?")
    elif (not 'time' in data_dict and not 'date' in data_dict):
      response = ("I can help you book the concierge time slot if you provide me the time and date :)")
  return (is_all_data_available, data_dict, response)

def fulfil_book_meeting_room_task(data):
  date = data['date']
  time = data['time']
  unit = data['unit']
  dur = data['duration']
  loc = data['location']
  response = "Successfully booked meeting room at " + loc + " " + unit + " on " + date + " at " + time + " for " + dur + " !"
  return (True, response)

def fulfil_book_concierge_time_task(data):
  date = data['date']
  time = data['time']
  response = "Successfully booked concierge time slot for " + date + " at " + time + " !"
  return (True, response)

def log_facilities_fault(input):
  case_number = random.randrange(999, 10000, 2)
  return f'Don\'t worry, I have logged your fault report with the facilities management department. The case number is #{case_number} and it would be saved under your fault reports in your profile. To add more details to the report, just click on this case number at your profile. Your contact has also been left with the department in case they need to contact you but is this urgent?'

RESPONSE_FILE = 'ContextWithDefaultResponse.json'

with open(SRC_DIR + '/' + RESPONSE_FILE) as json_data:
    responses = json.load(json_data)

# create a data structure to hold user context
context = {}
context_data = {}
smalltalk_chat_history = {}

# methods to for customised responses based on entities
def context_based_task_fulfilment(current_context, input, userID):
  is_custom_response = False
  response = ''
  if current_context == 'context.book_meeting_room':
    is_custom_response = True
    if userID in context_data:
      res = book_meeting_room_task(input, context_data[userID])
    else:
      res = book_meeting_room_task(input, data_dict={})

    #if there is no entities
    if len(res[1]) == 0:
        is_custom_response = False
        return (is_custom_response, response)

    context_data[userID] = res[1]
    canBeFulfilled = res[0]
    response = res[2]

    if canBeFulfilled:
      context[userID] = 'context.book_meeting_room.confirm_or_not'

  elif current_context == 'context.book_concierge_time':
    is_custom_response = True
    if userID in context_data:
      res = book_concierge_time_task(input, context_data[userID])
    else:
      res = book_concierge_time_task(input, data_dict={})

    #if there are no entities
    if len(res[1]) == 0:
        is_custom_response = False
        return (is_custom_response, response)

    context_data[userID] = res[1]
    canBeFulfilled = res[0]
    response = res[2]
    if canBeFulfilled:
      context[userID] = 'context.book_concierge_time.confirm_or_not'

  return (is_custom_response, response)

def intent_based_task_fulfilment(intent, input, userID):
  is_custom_response = False
  response = ''
  if intent =="task.book_meeting_room":
    res = book_meeting_room_task(input, data_dict={}, has_default_response=True)
    context_data[userID] = res[1]
    is_custom_response = res[0]
    response = res[2]
  elif intent == 'task.book_concierge_time':
    res = book_concierge_time_task(input, data_dict={}, has_default_response=True)
    context_data[userID] = res[1]
    is_custom_response = res[0]
    response = res[2]
  elif intent == 'task.log_facilities_fault':
    response = log_facilities_fault(input)
    context[userID] = "context.facilities_fault.urgent_or_not"
    is_custom_response = True
  elif intent == 'task.fix_facilities_fault':
    response = log_facilities_fault(input)
    context[userID] = "context.facilities_fault.urgent_or_not"
    is_custom_response = True
  elif intent == 'general.consent' and userID in context and context[userID] == 'context.book_meeting_room.confirm_or_not':
    res = fulfil_book_meeting_room_task(context_data[userID])
    is_custom_response = res[0]
    response = res[1]
    del context[userID]
    if userID in context_data:
        del context_data[userID]
  elif intent == 'general.consent' and userID in context and context[userID] == 'context.book_concierge_time.confirm_or_not':
    res = fulfil_book_concierge_time_task(context_data[userID])
    is_custom_response = res[0]
    response = res[1]
    del context[userID]
    if userID in context_data:
        del context_data[userID]
  elif intent == 'general.rejection':
    if userID in context:
        del context[userID]
    if userID in context_data:
        del context_data[userID]

  return (is_custom_response, response)

ACRONYMS = ["aor", "cmb"]
SLANGS = ["nope"]
'''
if len([i for i in ACRONYMS if i in sentence.lower()]) > 0:
    autocorrect = False
if autocorrect:
  corrector = Speller(fast=True)
  sentence = corrector(sentence)
  print(sentence, file=sys.stderr)
'''

def response(sentence, userID='123', show_details=False, autocorrect=True):

    add_input_num()
    add_input_num_since_training()
    results = classify_intent(sentence, userID)
    if show_details: print('user ID:', userID, file=sys.stderr)
    current_context = ''
    if userID in context:
      current_context = context[userID]
    if show_details: print('current context:', current_context, file=sys.stderr)
    if show_details: print(results, file=sys.stderr)

    #if we have a classification then find the matching intent tag
    if results:
        # loop as long as there are matches to process
        while results:

            if results[0][0] == 'context' or results[0][0] == 'smalltalk.dialogpt':
              break

            for i in responses['responses']:
                # find a tag matching the first result
                if i['tag'] == results[0][0]:

                    # check if this intent is contextual and applies to this user's conversation
                    if not 'context_filter' in i or \
                        (userID in context and 'context_filter' in i and i['context_filter'] == context[userID]):
                        if show_details: print('tag:', i['tag'], file=sys.stderr)
                        if show_details: print('tag:', results[0][1], file=sys.stderr)
                        if show_details: print('current context:', current_context, file=sys.stderr)

                        #delete smalltalk chat history
                        if userID in smalltalk_chat_history:
                            del smalltalk_chat_history[userID]

                        #try to let bot fulfil the task using entities
                        res = intent_based_task_fulfilment(results[0][0], sentence, userID)
                        respondedFromIntentBasedTask = res[0]

                        # set context for this intent if necessary
                        if 'context_set' in i:
                          if show_details: print('context set:', i['context_set'], file=sys.stderr)
                          context[userID] = i['context_set']

                        #give random response from the intent since not enough entities given
                        if not respondedFromIntentBasedTask and 'general' in i['tag']:
                            add_input(sentence, userID, True, i['tag'], None)
                            return random.choice(i['responses']) + " " + random.choice(EMOJI_RESPONSE_POS)
                        elif not respondedFromIntentBasedTask:
                            add_input(sentence, userID, True, i['tag'], None)
                            return random.choice(i['responses'])
                        else:
                            add_input(sentence, userID, True, i['tag'], None)
                            return res[1]

            results.pop(0)

    #try to fulfil task based on entities and context set previously
    #for context without intent identification
    res = context_based_task_fulfilment(current_context, sentence, userID)
    respondedFromContextBasedTask = res[0]
    if respondedFromContextBasedTask:

        #delete smalltalk chat history
        if userID in smalltalk_chat_history:
            del smalltalk_chat_history[userID]

        add_input(sentence, userID, True, 'context', None)
        return res[1]

    smallTalkResponse = getSmallTalkResponse(userID, smalltalk_chat_history, sentence)
    if not smallTalkResponse == '':
        #delete context since smalltalk engaged
        if userID in context:
            del context[userID]
        if userID in context_data:
            del context_data[userID]
        add_input(sentence, userID, True, 'smalltalk.dialogpt', None)
        return smallTalkResponse

    sentiment = classify_sentiment(sentence, userID)
    if not sentiment == '':
        #delete smalltalk chat history
        if userID in smalltalk_chat_history:
            del smalltalk_chat_history[userID]

        if sentiment in EMOJI_RESPONSE_NEG:
            tagged_sentiment = 0
        elif sentiment in EMOJI_RESPONSE_POS:
            tagged_sentiment = 1
        else:
            tagged_sentiment = None
        add_input(sentence, userID, True, 'sentiment.emoji', tagged_sentiment)
        return sentiment

    add_input(sentence, userID, False, None, None)
    update_tagging_status(userID, True)
    add_incorrect_num()
    add_incorrect_num_since_training()
    return ('Sorry but I did not understand what you just said. Forgive me but I am still learning.')
