from flask import Flask, render_template, request, url_for, redirect, session, flash
import functools
from chatbot import response, context, context_data
from databaseController import *
from intentClassifierTrainer import *
import sys
from databaseController import *
from sentimentAnalyserTrainer import *

app = Flask('__name__')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "name" not in session:
            return redirect(url_for("sign_up"))
        elif 'user_id' not in session:
            return redirect(url_for("sign_up"))
        return func(*args, **kwargs)

    return secure_function

def admin_login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "admin_username" not in session:
            return redirect(url_for("admin_login"))
        if "admin_username" in session and 'admin_password' in session:
            isAdmin = checkIfAdmin(session['admin_username'], session['admin_password'])
            if not isAdmin:
                return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return secure_function

@app.route("/chat", methods=["GET"])
@login_required
def home():
  userID = session['user_id']
  name = session['name']
  if userID in context:
      del context[userID]
  if userID in context_data:
      del context_data[userID]
  return render_template("home.html", name=name.capitalize())

@app.route("/", methods=["GET", "POST"])
def sign_up():
    #possible bug because sometimes user already exist but still prompt for sign up
    if "name" in session and "user_id" in session:
        return home()

    if request.method == "POST":
        name = request.form.get('name')

        if len(name) < 5:
            flash("Please input your full name!")

        session['name'] = name
        user_id = add_user(name)
        session['user_id'] = str(user_id)
        return redirect(url_for('home'))

    return render_template("login.html")

@app.route("/logout", methods=["GET"])
def logout():
    if "name" in session:
        session.pop('name', None)
    if "user_id" in session:
        session.pop("user_id", None)
    return sign_up()

@app.route("/get", methods=["GET"])
@login_required
def get_bot_response():
  userText = request.args.get('msg')
  return response(userText, userID=session['user_id'], show_details=True)

@app.route("/report-input", methods=["GET"])
@login_required
def report_input():
    isExistingInput = untag_last_input(session['user_id'])
    if isExistingInput:
        add_incorrect_num()
        add_incorrect_num_since_training()
        return 'is Existing Input'
    else:
        return 'is Not Existing Input'

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if "admin_username" in session and "admin_password" in session:
        isAdmin = checkIfAdmin(session['admin_username'], session['admin_password'])
        del session['admin_username']
        del session['admin_password']

    else:
        if request.method == "POST":
            username = request.form.get('adminInputUsername')
            password = request.form.get('adminInputPassword')

            session['admin_username'] = username
            session['admin_password'] = password
            isAdmin = checkIfAdmin(session['admin_username'], session['admin_password'])
            if isAdmin:
                return redirect(url_for('admin_dashboard'))

    return render_template("adminLogin.html")

@app.route("/dashboard", methods=["GET", "POST"])
@admin_login_required
def admin_dashboard():
    need_retraining = get_model_status()
    users = get_all_users()
    filtered_users = get_users_need_tagging()
    isFiltered = False
    if request.method == "POST":
        isFilteredFromForm = request.form.get('isFiltered')
        if isFilteredFromForm == 'False':
            isFiltered = True
        else:
            isFiltered = False

    return render_template('adminDashboard.html', users=enumerate(users), filtered_users=enumerate(filtered_users), isFiltered=isFiltered, need_retraining=need_retraining)

@app.route("/tag-conversation", methods=["GET"])
@admin_login_required
def tag_conversation():
    userID = request.args.get('userID', None)
    username = get_username(userID)
    log = get_user_conversation_log(userID)
    list_of_log = list(log)
    tags = get_all_tags()
    list_of_tags = list(tags)
    log_len = len(list_of_log)
    return render_template('conversationLog.html', currentFilter="Show All", userID=userID, username=username, log=list_of_log, tags=list_of_tags, log_len=log_len)

@app.route("/tag-conversation-past-month", methods=["GET"])
@admin_login_required
def tag_conversation_past_month():
    userID = request.args.get('userID', None)
    username = get_username(userID)
    #past month
    list_of_log = get_user_conversation_log_past_days(userID, 31)
    tags = get_all_tags()
    list_of_tags = list(tags)
    log_len = len(list_of_log)
    return render_template('conversationLog.html', currentFilter="Past Month", userID=userID, username=username, log=list_of_log, tags=list_of_tags, log_len=log_len)

@app.route("/tag-conversation-past-week", methods=["GET"])
@admin_login_required
def tag_conversation_past_week():
    userID = request.args.get('userID', None)
    username = get_username(userID)
    #past week
    list_of_log = get_user_conversation_log_past_days(userID, 7)
    tags = get_all_tags()
    list_of_tags = list(tags)
    log_len = len(list_of_log)
    return render_template('conversationLog.html', currentFilter="Past Week", userID=userID, username=username, log=list_of_log, tags=list_of_tags, log_len=log_len)

@app.route("/tag-conversation-past-year", methods=["GET"])
@admin_login_required
def tag_conversation_past_year():
    userID = request.args.get('userID', None)
    username = get_username(userID)
    #past week
    list_of_log = get_user_conversation_log_past_days(userID, 365)
    tags = get_all_tags()
    list_of_tags = list(tags)
    log_len = len(list_of_log)
    return render_template('conversationLog.html', currentFilter="Past Year", userID=userID, username=username, log=list_of_log, tags=list_of_tags, log_len=log_len)

@app.route("/tag-conversation-untagged", methods=["GET"])
@admin_login_required
def tag_conversation_untagged():
    userID = request.args.get('userID', None)
    username = get_username(userID)
    #untagged only
    list_of_log = get_user_conversation_log_untagged(userID)
    tags = get_all_tags()
    list_of_tags = list(tags)
    log_len = len(list_of_log)
    return render_template('conversationLog.html', currentFilter="Untagged Only", userID=userID, username=username, log=list_of_log, tags=list_of_tags, log_len=log_len)

@app.route("/submit-tags/<userID>", methods=["POST"])
@admin_login_required
def submit_tags(userID):
    log = get_user_conversation_log(userID)
    list_of_log = list(log)
    tags = get_all_tags()
    list_of_tags = list(tags)
    for entry in list_of_log:
        id = entry['_id']
        tag = request.form.get(str(id))
        if not tag == 'Choose Tag':
            #update input's tag
            update_input_tag(id, tag)
            #update input's isIdentified to True
            update_is_identified(id, True)
            #update user tagging status if necessary
            check_and_update_tagging_status(userID)
            #update retraining status only when a tag has been added (unidentified intent) or existing tag was edited (likely incorrectly identified intent)
            update_model_status(True)
            #update json
            input = get_user_input(id)
            add_tagged_data_in_json_training_file(tag, input)
    return redirect(url_for('tag_conversation_past_month', userID=userID))

@app.route("/tag-sentiment", methods=["GET"])
@admin_login_required
def tag_sentiment():
    filtered_log = get_inputs_need_sentiment_tagging()
    need_training = check_if_need_train_sentiment()
    return render_template('sentimentLog.html', currentFilter="Show All", log=filtered_log[::-1], log_len=len(filtered_log), need_training=need_training)

@app.route("/tag-sentiment-past-week", methods=["GET"])
@admin_login_required
def tag_sentiment_past_week():
    filtered_log = get_inputs_need_sentiment_tagging_past_days(7)
    need_training = check_if_need_train_sentiment()
    return render_template('sentimentLog.html', currentFilter="Past Week", log=filtered_log[::-1], log_len=len(filtered_log), need_training=need_training)

@app.route("/tag-sentiment-past-month", methods=["GET"])
@admin_login_required
def tag_sentiment_past_month():
    filtered_log = get_inputs_need_sentiment_tagging_past_days(31)
    need_training = check_if_need_train_sentiment()
    return render_template('sentimentLog.html', currentFilter="Past Month", log=filtered_log[::-1], log_len=len(filtered_log), need_training=need_training)

@app.route("/tag-sentiment-past-half-year", methods=["GET"])
@admin_login_required
def tag_sentiment_past_half_year():
    filtered_log = get_inputs_need_sentiment_tagging_past_days(183)
    need_training = check_if_need_train_sentiment()
    return render_template('sentimentLog.html', currentFilter="Past Half Year", log=filtered_log[::-1], log_len=len(filtered_log), need_training=need_training)

@app.route("/tag-sentiment-past-year", methods=["GET"])
@admin_login_required
def tag_sentiment_past_year():
    filtered_log = get_inputs_need_sentiment_tagging_past_days(365)
    need_training = check_if_need_train_sentiment()
    return render_template('sentimentLog.html', currentFilter="Past Year", log=filtered_log[::-1], log_len=len(filtered_log), need_training=need_training)

@app.route("/tag-sentiment-untagged", methods=["GET"])
@admin_login_required
def tag_sentiment_untagged():
    filtered_log = get_inputs_need_sentiment_tagging_untagged()
    need_training = check_if_need_train_sentiment()
    return render_template('sentimentLog.html', currentFilter="Untagged Only", log=filtered_log[::-1], log_len=len(filtered_log), need_training=need_training)

@app.route("/submit-sentiment-tags", methods=["POST"])
@admin_login_required
def submit_sentiment_tags():
    filtered_log = get_inputs_need_sentiment_tagging()
    input_list = []
    for entry in filtered_log:
        id = entry['_id']
        sentiment = request.form.get(str(id))
        input = get_user_input(id)
        if not sentiment == 'Choose Sentiment':
            #update input's tag
            if sentiment == 'Positive':
                update_input_sentiment(id, 1)
                #update csv!!!
                input_list.append((1, input))

            elif sentiment == 'Negative':
                update_input_sentiment(id, 0)
                #update csv!!!
                input_list.append((0, input))

            elif sentiment == 'Neutral':
                update_input_sentiment(id, None)
                input_list.append((None, input))

    if len(input_list) > 0:
        #update need retrain sentiment model
        update_need_train_sentiment(True)
        #update csv!!!
        add_tagged_data_in_csv_training_file(input_list)

    return redirect(url_for('tag_sentiment'))

@app.route("/retrain-sentiment", methods=["POST"])
@admin_login_required
def retrain_sentiment():
    update_need_train_sentiment(False)

    #update json and retrain
    train_sentiment_model()

    #update need to reload sentiment model status when retrained
    update_need_reload_sentiment_analyser(True)
    return tag_sentiment()

@app.route("/retrain", methods=["POST"])
@admin_login_required
def retrain():
    update_model_status(False)
    #update json and retrain
    train_data()

    #update database statistics and status
    update_need_reload_model(True)
    refresh_incorrect_num_since_training()
    refresh_input_num_since_training()
    return admin_dashboard()

@app.route("/delete-log", methods=["GET"])
@admin_login_required
def delete_log():
    userID = request.args.get('userID', None)
    delete_conversation_log(userID)
    update_tagging_status(userID, False)
    return redirect(url_for('tag_conversation', userID=userID))

@app.route("/user-info", methods=["GET"])
@admin_login_required
def user_info():
    userID = request.args.get("userID", None)
    username = get_username(userID)
    log = get_user_conversation_log(userID)
    list_of_log_len = len(list(log))
    unidentified_log = get_user_inputs_need_tagging(userID)
    list_of_unidentified_log_len = len(list(unidentified_log))
    return render_template('userInfo.html', username=username, log_len=list_of_log_len, unidentified_log_len=list_of_unidentified_log_len)

def filterTags(tag):
    if 'sentiment.emoji' == tag['tag'] or 'context' == tag['tag'] or 'smalltalk.dialogpt' == tag['tag']:
        return False
    else:
        return True

@app.route("/tags", methods=["GET", "POST"])
@admin_login_required
def tags():
    tags = get_all_tags()
    tags_list = list(tags)
    filtered_list = filter(filterTags, tags_list)
    if request.method == 'POST':
        added_tag = request.form.get('tagInput')
        if 'sentiment' in added_tag or 'context' in added_tag:
            flash("Please do not add any tags for sentiment or context! One allowed for each and there is already the tags 'sentiment.emoji' and 'context' for each.")
            tags = get_all_tags()
            tags_list = list(tags)
            filtered_list = filter(filterTags, tags_list)
            return render_template("tags.html", tags=enumerate(filtered_list), scrollTo="main")
        if len([tag for tag in tags if tag == added_tag]) > 0:
            flash("Please do not have repeating names for tags to avoid confusion!")
            tags = get_all_tags()
            tags_list = list(tags)
            filtered_list = filter(filterTags, tags_list)
            return render_template("tags.html", tags=enumerate(filtered_list), scrollTo="main")

        id = add_tag(added_tag)
        tags = get_all_tags()
        tags_list = list(tags)
        filtered_list = filter(filterTags, tags_list)
        return render_template("tags.html", tags=enumerate(filtered_list), scrollTo=id)

    return render_template("tags.html", tags=enumerate(filtered_list), scrollTo="main")

@app.route("/delete-tag", methods=["GET"])
@admin_login_required
def delete_a_tag():
    tag_id = request.args.get("id", None)
    tag = get_tag(tag_id)['tag']
    delete_tag(tag_id)

    inputs = get_all_inputs()
    inputs_list = list(inputs)
    for input in inputs_list:
        if input['tag'] == tag:
            #update input tag to None and isIdentified to False
            update_input_tag(input['_id'], None)
            update_is_identified(input['_id'], False)
            #update user tagging Status
            check_and_update_tagging_status(input['user_id'])
            #update need retraining status if all inputs in database considered
            #update_model_status(True)

    #update json
    isJsonChanged = delete_tag_from_json_training_file(tag)
    if isJsonChanged:
        update_model_status(True)

    return tags()

@app.route("/edit-tag", methods=["POST"])
@admin_login_required
def edit_a_tag():
    tag_id = request.form.get("id")
    oldTag = get_tag(tag_id)['tag']
    tags = get_all_tags()
    if request.form['formButton'] == 'submit':
        new_tag_name = request.form.get("newTagName")
        if 'sentiment' in new_tag_name or 'context' in new_tag_name:
            flash("Please do not add any tags for sentiment or context! One allowed for each and there is already the tags 'sentiment.emoji' and 'context' for each.")
            tags = get_all_tags()
            tags_list = list(tags)
            filtered_list = filter(filterTags, tags_list)
            return render_template("tags.html", tags=enumerate(filtered_list), scrollTo="main")
        #check if new tag overlaps with another existing tag name
        if len([tag for tag in tags if tag == new_tag_name]) > 0:
            flash("Please do not have repeating names for tags to avoid confusion!")
            tags = get_all_tags()
            tags_list = list(tags)
            filtered_list = filter(filterTags, tags_list)
            return render_template("tags.html", tags=enumerate(filtered_list), scrollTo="main")

        update_tag(new_tag_name, tag_id)
        #edit json_data
        edit_tag_in_json_training_file(oldTag, new_tag_name)

    tags = get_all_tags()
    tags_list = list(tags)
    filtered_list = filter(filterTags, tags_list)
    return render_template("tags.html", tags=enumerate(filtered_list), scrollTo=tag_id)

@app.route("/performance", methods=["GET"])
@admin_login_required
def performance():
    error_threshold = get_error_threshold()

    num_inputs_all = get_input_num()
    num_incorrect_all = get_incorrect_num()
    num_inputs_since_last_training = get_input_num_since_training()
    num_incorrect_since_last_training = get_incorrect_num_since_training()
    percentage_correct_all = round((num_inputs_all - num_incorrect_all) / num_inputs_all * 100, 1)
    if num_inputs_since_last_training == 0:
        percentage_correct_since_last_training = 100
    else:
        percentage_correct_since_last_training = round((num_inputs_since_last_training - num_incorrect_since_last_training) / num_inputs_since_last_training * 100, 1)

    num_inputs_last_month = get_input_num_last_month()
    num_incorrect_last_month = get_incorrect_num_last_month()
    if num_inputs_last_month == 0:
        percentage_correct_last_month = 100
    else:
        percentage_correct_last_month = round((num_inputs_last_month - num_incorrect_last_month) / num_inputs_last_month * 100, 1)

    num_inputs_last_week = get_input_num_last_week()
    num_incorrect_last_week = get_incorrect_num_last_week()
    if num_inputs_last_week == 0:
        percentage_correct_last_week = 100
    else:
        percentage_correct_last_week = round((num_inputs_last_week - num_incorrect_last_week) / num_inputs_last_week * 100, 1)

    return render_template('statistics.html', error_threshold=error_threshold, percentage_correct_all=percentage_correct_all, percentage_correct_since_last_training=percentage_correct_since_last_training, percentage_correct_last_month=percentage_correct_last_month, percentage_correct_last_week=percentage_correct_last_week)

@app.route("/error-threshold", methods=["POST"])
@admin_login_required
def error_threshold():
    try:
        new_error_threshold = float(request.form.get("error_threshold"))
    except:
        flash("Please only input a number between 0 and 1.")
    if (new_error_threshold > 1.0) or (new_error_threshold < 0.0):
        flash("Please only input a number between 0 and 1.")
    update_error_threshold(new_error_threshold)
    update_need_reload_error_threshold(True)
    return performance()


if __name__ == "__main__":
  app.run(debug=True)
