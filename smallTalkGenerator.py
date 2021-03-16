from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from sentimentAnalyser import classify_sentiment

gpt_tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
gpt_model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

previous_response = {}
previous_input = {}

def getSmallTalkResponse(userID, smalltalk_chat_history, sentence):
    # encode the new user input, add the eos_token and return a tensor in Pytorch
    new_user_input_ids = gpt_tokenizer.encode(sentence + gpt_tokenizer.eos_token, return_tensors='pt')

    # append the new user input tokens to the chat history
    if userID in smalltalk_chat_history:
        bot_input_ids = torch.cat([ smalltalk_chat_history[userID], new_user_input_ids], dim=-1)
    else:
        if userID in previous_response:
            del previous_response[userID]
        if userID in previous_input:
            del previous_input[userID]
        bot_input_ids = new_user_input_ids
    # generated a response while limiting the total chat history to 1000 tokens,
    smalltalk_chat_history[userID] = gpt_model.generate(bot_input_ids, max_length=1000, pad_token_id=gpt_tokenizer.eos_token_id)

    # pretty print last ouput tokens from bot
    chat_history_ids = smalltalk_chat_history[userID]

    current_response = gpt_tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    if userID in previous_response and userID in previous_input and current_response == previous_response[userID] and not previous_input[userID] == sentence:
      return ''
    previous_response[userID] = current_response
    previous_input[userID] = sentence

    return current_response + " " + classify_sentiment(sentence, userID)
