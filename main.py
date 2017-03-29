import telebot, json, requests
from watson_developer_cloud import ConversationV1
import time

bot = telebot.TeleBot("352103827:AAG1fNzI5S3M_Xg0B5cnhFKP3w6NwJHxi24")
conversation = ConversationV1(
    username='de3f5464-f9da-46e0-b517-203d4e95237c',
    password='fwvhVMKSFyP0',
    version='2017-03-28')
workspace_id = 'edbf9f5c-938b-4470-b3fd-24b42efed20a'

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    response = conversation.message(workspace_id=workspace_id, message_input={
        'text': message.text})
    bot.reply_to(message, 'Hola, soy Watson, un bot con principios de machine learning, lo cual me ayuda a aprender de mis interacciones con humanos. ¿En qué te ayudo?')

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    response = conversation.message(workspace_id=workspace_id, message_input={
        'text': message.text})
    try:
        if 'hora' in response['intents'][0]['intent']:
            bot.reply_to(message, response['output']['text'][0].format(time.strftime('%H:%M:%S')))
        elif 'chiste' in response['intents'][0]['intent']:
            resp = requests.get('http://api.icndb.com/jokes/random')
            if resp.status_code != 200:
                bot.reply_to(message, response['output']['text'])
            else:
                bot.reply_to(message, resp.json()['value']['joke'].replace('&quot;', '\"'))
        else:
            bot.reply_to(message, response['output']['text'])
    except(IndexError) as err:
        bot.reply_to(message, response['output']['text'])
        print(response)
        print(err)
    finally:
        pass

bot.polling()