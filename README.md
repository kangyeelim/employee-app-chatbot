# Chatbot App
Chatbot for workspace productivity for employee apps.
(on going)

## Usage

* Chat with 'Jonathan' to help complete tasks
* Access the admin dashboard to retrain intent classification and sentiment analysis model

## Setup your own

You would need to make sure python and pip is downloaded. To do the following commands, download Git if on windows and git bash into the root project directory. Also, this app works with MongoDB so to run it, make an account for MongoDB. Then create a project for this and create a database called 'chatbot-prototype-1' for this project. Add 'processed_tweets.csv' files from Google Drive (https://drive.google.com/drive/folders/1jaNeITz1sszPDD9aS9gDdhDFrKnuPdUr?usp=sharing) under the directory /model. 

# To connect to database
* Create a file called .env add MONGO_DB=<url> where <url> is the url from your project in MongoDB
* To get the <url>, go to project in MongoDB to see Clusters > press 'connect' > press 'Connect your application to your cluster using MongoDB native drivers' > use the url in that page

# Set up admin credentials
* Make a collection called 'users' and create an entry with the 'username' = <define your admin username>, 'password' = <define your admin password>, 'isAdmin' = true

```bash
# Install virtualenv
$ pip install virtualenv

#Create new virtual environment inside directory depending on Python version below
#Python 2:
$ virtualenv env
#Python 3:
$ python3 -m venv env

#Activate virtualenv (for windows Git bash)
$ source ./env/Scripts/activate

# Install all other dependencies for the project to work
$ pip install -r requirements.txt

#To run application
$ python app.py

#Follow Flask instructions shown to go to link

```

### DB Schema
Uses MongoDB

| Schema |      Name      |   
|--------|----------------|
| 1 | inputs          |
| 2 | model_status        |
| 3 | tags | table |  
| 4 | users         |

Table "users"
|Column |       Type         | Nullable |     
|------|------------------|----------|
| _id    |                    | not null |  
| username  | String          | not null |		
| password |      String      |  null |				
| isAdmin | Boolean           | not null |					
| needsTagging  | Boolean           | null |				
| need_reload_model  | Boolean          | null |				
| need_reload_error_threshold  |      Boolean     | null |		
| need_reload_sentiment_analyser |     Boolean      | null |							   

Table "inputs"
|Column |       Type         | Nullable |             
|------|------------------|----------|
| _id    |                    | not null |  
| input| String           | not null |					
| user_id  | String          | not null |					
| isIdentified  |   Boolean        | not null |
| tag  |   String        |  null |									   
| original_isIdentified  |   Boolean        | not null |		
| sentiment  |   String        | null |		
| created_at  |   Date        | not null |		

Table "sessions"
|Column |       Type         | Nullable |              Default              |
|------|------------------|----------|-------------------------------------------|
| _id    |                    | not null |  |
| question| String           | not null |					null			   |
| options  | Array          | not null |					null			   |
| answer  | Number          | not null |					null			   |
| timestamp  |           | not null |								   |

Table "model_status"
|Column |       Type         | Nullable |
|------|------------------|----------|
| _id    |                    | not null |  
| need_training  | Boolean        | not null |		
| num_inputs_all |      Int64      | not null |				
| num_incorrect_all | Int64           | not null |			
| num_inputs_since_last_training  |     Int64      | not null |								   
| num_incorrect_since_last_training  |    Int64       | not null |								   
| error_threshold  |    Double      | not null |								   
| need_sentiment_training  |     Boolean      | not null |								   

Table "tags"
|Column |       Type         | Nullable |      
|------|------------------|----------|
| _id    |                    | not null |  
| tag| String           | not null |			
