import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime

#os.environ['MONGO_DB'] = ''

load_dotenv()

if not os.getenv("MONGO_DB"):
    raise RuntimeError("MONGO_DB is not set")

MONGO_DB = os.getenv("MONGO_DB")

client = MongoClient(MONGO_DB)
db = client['chatbot-prototype-1']

# Database methods to collect user inputs
def add_input(input, userID, isIdentified, tag, sentiment):
    entry = {
        'input':input,
        'user_id': userID,
        'isIdentified': isIdentified,
        'tag': tag,
        'original_isIdentified': isIdentified,
        'sentiment': sentiment,
        'created_at': datetime.datetime.utcnow()
    }
    input_id = db.inputs.insert_one(entry).inserted_id
    return input_id

def checkIfAdmin(username, password):
    checkUser = db.users.find_one({"username": username})
    checkPw = db.users.find_one({"password": password})
    user = db.users.find_one({"username": username, "password": password})
    return checkUser and checkPw and user['isAdmin']

def add_user(username, needsTagging=False):
    entry = {
        'username': username,
        'password': None,
        'needsTagging': needsTagging,
        'isAdmin': False,
        'need_reload_model': False,
        'need_reload_error_threshold': False,
        'need_reload_sentiment_analyser': False
    }
    input_id = db.users.insert_one(entry).inserted_id
    return input_id

def get_all_users():
    users = db.users.find({"isAdmin": False})
    return users

def get_username(userID):
    user = db.users.find_one({"_id": ObjectId(userID)})
    return user['username']

def get_users_need_tagging():
    users = db.users.find({"isAdmin": False, "needsTagging": True})
    return users

def update_tagging_status(userID, needsTagging):
    user = db.users.find_one_and_update({"_id": ObjectId(userID)}, {
    "$set": {"needsTagging": needsTagging}
    }, upsert=True)

def get_user_conversation_log(userID):
    log = db.inputs.find({"user_id": userID})
    return log

def update_input_tag(id, tag):
    entry = db.inputs.find_one_and_update({"_id":ObjectId(id)}, {
    "$set": {"tag": tag}
    }, upsert=True)

def update_is_identified(id, isIdentified):
    entry = db.inputs.find_one_and_update({"_id":ObjectId(id)}, {
    "$set": {"isIdentified": isIdentified}
    }, upsert=True)

def check_and_update_tagging_status(userID):
    entry = db.inputs.find({"user_id":userID, "isIdentified": False})
    if len(list(entry)) == 0:
        update_tagging_status(userID, False)
    else:
        update_tagging_status(userID, True)

def get_all_tags():
    tags = db.tags.find()
    return tags

def get_model_status():
    status = db.model_status.find()
    need_training = list(status)[0]['need_training']
    return need_training

def update_model_status(status):
    status = db.model_status.update_one({}, {
    "$set": {"need_training": status}
    }, upsert=True)

def delete_conversation_log(userID):
    db.inputs.delete_many({"user_id": userID})

def get_user_inputs_need_tagging(userID):
    log = db.inputs.find({"user_id":userID, "isIdentified": False})
    return log

def add_tag(tag):
    id = db.tags.insert_one({"tag":tag}).inserted_id
    return id

def update_tag(tag, id):
    db.tags.update_one({"_id":ObjectId(id)}, {
    "$set": {"tag":tag}
    }, upsert=True)

def delete_tag(id):
    db.tags.delete_one({"_id":ObjectId(id)})

def get_all_inputs():
    inputs = db.inputs.find()
    return inputs

def get_tag(id):
    tag = db.tags.find_one({"_id":ObjectId(id)})
    return tag

def untag_last_input(userID):
    inputs = db.inputs.find({"user_id": userID}).sort([("_id", -1)]).limit(1)
    for input in inputs:
        db.inputs.update_one({"_id": ObjectId(input["_id"])}, {
            "$set": {"tag": None, "isIdentified": False, "original_isIdentified": False}
            }, upsert=True)
        update_tagging_status(userID, True)
        return True
    return False

def get_user_input(id):
    input = db.inputs.find_one({"_id":ObjectId(id)})
    return input['input']

def add_input_num():
    status = db.model_status.update_one({}, {
    "$inc": {"num_inputs_all": 1}
    }, upsert=True)

def add_input_num_since_training():
    status = db.model_status.update_one({}, {
    "$inc": {"num_inputs_since_last_training": 1}
    }, upsert=True)

def add_incorrect_num():
    status = db.model_status.update_one({}, {
    "$inc": {"num_incorrect_all": 1}
    }, upsert=True)

def add_incorrect_num_since_training():
    status = db.model_status.update_one({}, {
    "$inc": {"num_incorrect_since_last_training": 1}
    }, upsert=True)

def refresh_input_num_since_training():
    status = db.model_status.update_one({}, {
    "$set": {"num_inputs_since_last_training": 0}
    }, upsert=True)

def refresh_incorrect_num_since_training():
    status = db.model_status.update_one({}, {
    "$set": {"num_incorrect_since_last_training": 0}
    }, upsert=True)

def get_input_num():
    status = db.model_status.find()
    return status[0]["num_inputs_all"]

def get_input_num_since_training():
    status = db.model_status.find()
    return status[0]["num_inputs_since_last_training"]

def get_incorrect_num():
    status = db.model_status.find()
    return status[0]["num_incorrect_all"]

def get_incorrect_num_since_training():
    status = db.model_status.find()
    return status[0]["num_incorrect_since_last_training"]

def get_input_num_last_month():
    inputs = db.inputs.find({
    'created_at': {
        '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=31),
        '$lt': datetime.datetime.utcnow()
    }
    })
    len_inputs = len(list(inputs))
    return len_inputs

def get_incorrect_num_last_month():
    inputs = db.inputs.find({
    'created_at': {
        '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=31),
        '$lt': datetime.datetime.utcnow()
    },
    'original_isIdentified': False
    })
    len_inputs = len(list(inputs))
    return len_inputs

def get_input_num_last_week():
    inputs = db.inputs.find({
    'created_at': {
        '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=7),
        '$lt': datetime.datetime.utcnow()
    }
    })
    len_inputs = len(list(inputs))
    return len_inputs

def get_incorrect_num_last_week():
    inputs = db.inputs.find({
    'created_at': {
        '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=7),
        '$lt': datetime.datetime.utcnow()
    },
    'original_isIdentified': False
    })
    len_inputs = len(list(inputs))
    return len_inputs

def get_user_conversation_log_past_days(userID, days):
    inputs = db.inputs.find({
    'created_at': {
        '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=days),
        '$lt': datetime.datetime.utcnow()
    },
    "user_id": userID
    })
    return list(inputs)

def get_user_conversation_log_untagged(userID):
    inputs = db.inputs.find({"user_id": userID, "isIdentified": False})
    return list(inputs)

def get_error_threshold():
    status = db.model_status.find()
    return status[0]["error_threshold"]

def update_error_threshold(new_dec):
    status = db.model_status.update_one({}, {
    "$set": {"error_threshold": new_dec}
    }, upsert=True)

def update_input_sentiment(id, sentiment):
    entry = db.inputs.find_one_and_update({"_id":ObjectId(id)}, {
    "$set": {"sentiment": sentiment}
    }, upsert=True)

def get_inputs_need_sentiment_tagging():
    inputs = db.inputs.find({ "$or": [ { "tag": "sentiment.emoji" }, { "tag": {"$regex" : ".*smalltalk.*"} } ] })
    return list(inputs)

def get_inputs_need_sentiment_tagging_past_days(days):
    inputs = db.inputs.find({ 'created_at': {
        '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=days),
        '$lt': datetime.datetime.utcnow()
    }, "$or": [ { "tag": "sentiment.emoji" }, { "tag": {"$regex" : ".*smalltalk.*"} } ] })
    return list(inputs)

def get_inputs_need_sentiment_tagging_untagged():
    inputs = db.inputs.find({ "sentiment": None, "$or": [ { "tag": "sentiment.emoji" }, { "tag": {"$regex" : ".*smalltalk.*"} } ] })
    return list(inputs)

def check_if_need_train_sentiment():
    status = db.model_status.find()
    need_training = list(status)[0]['need_training_sentiment']
    return need_training

def update_need_train_sentiment(bool):
    status = db.model_status.update_one({}, {
    "$set": {"need_training_sentiment": bool}
    }, upsert=True)

def check_if_need_reload_sentiment_analyser(userID):
    users = db.users.find({"_id": ObjectId(userID), "need_reload_sentiment_analyser": True})
    if len(list(users)) == 1:
        return True
    return False

#change to each user or global?
def update_need_reload_sentiment_analyser(bool):
    status = db.users.update_many({"isAdmin": False}, {
    "$set": {"need_reload_sentiment_analyser": bool}
    }, upsert=True)

def check_if_need_reload_error_threshold(userID):
    users = db.users.find({"_id": ObjectId(userID), "need_reload_error_threshold": True})
    if len(list(users)) == 1:
        return True
    return False

def update_need_reload_error_threshold(bool):
    status = db.users.update_many({"isAdmin": False}, {
    "$set": {"need_reload_error_threshold": bool}
    }, upsert=True)

def check_if_need_reload_model(userID):
    users = db.users.find({"_id": ObjectId(userID), "need_reload_model": True})
    if len(list(users)) == 1:
        return True
    return False

def update_need_reload_model(status):
    status = db.users.update_many({"isAdmin": False}, {
    "$set": {"need_reload_model": status}
    }, upsert=True)

def update_need_reload_model_for_user(status, userID):
    status = db.users.update_one({"_id": ObjectId(userID), "isAdmin": False}, {
    "$set": {"need_reload_model": status}
    }, upsert=True)

def update_need_reload_error_threshold_for_user(status, userID):
    status = db.users.update_one({"_id": ObjectId(userID), "isAdmin": False}, {
    "$set": {"need_reload_error_threshold": status}
    }, upsert=True)

def update_need_reload_sentiment_analyser_for_user(status, userID):
    status = db.users.update_one({"_id": ObjectId(userID), "isAdmin": False}, {
    "$set": {"need_reload_sentiment_analyser": status}
    }, upsert=True)
