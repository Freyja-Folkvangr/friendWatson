import telebot, json, requests
from telebot import types
from watson_developer_cloud import ConversationV1, LanguageTranslatorV2
import time
from phue import Bridge

b = Bridge('172.27.0.116')
b.connect()

def getLights():
    lights = b.get_light_objects('name')
    for light in lights:
        yield light

bot = telebot.TeleBot("352103827:AAG1fNzI5S3M_Xg0B5cnhFKP3w6NwJHxi24")
conversation = ConversationV1(
    username='de3f5464-f9da-46e0-b517-203d4e95237c',
    password='fwvhVMKSFyP0',
    version='2017-03-28')
workspace_id = 'edbf9f5c-938b-4470-b3fd-24b42efed20a'

translator = LanguageTranslatorV2(
   username='3fac851e-8f83-4b59-b62a-1494a79aef86',
   password='2krMxrkYIBkS')


knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts

privilegedChats = [42789923]

commands = {  # command description used in the "help" command
              'start': 'Usar el bot',
              'help': 'Da informacion de los comandos disponibles',
}

hideBoard = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard

# error handling if user isn't known yet
# (obsolete once known users are saved to file, because all users
#   had to use the /start command and are therefore known to the bot)
def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        knownUsers.append(uid)
        userStep[uid] = 0
        print ("Este usuario no escribio /start {}".format(uid))
        return 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    def command_start(message):
        cid = message.chat.id
        if cid not in knownUsers:  # if user hasn't used the "/start" command yet:
            knownUsers.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
            userStep[cid] = 0  # save user id and his current "command level", so he can use the "/getImage" command
            command_help(message)  # show the new user the help page
            bot.reply_to(message, 'Hola, soy Watson, un bot con principios de machine learning, lo cual me ayuda a aprender de mis interacciones con humanos. ¿En qué te ayudo?')
        else:
            bot.send_message(cid, "Ya nos conocemos!")

@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "Estos comandos podrían ser útiles: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page

@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def lightSelection(m):
    cid = m.chat.id
    text = m.text
    lights = []

    for item in getLights():
        lights.append(item)

    # for some reason the 'upload_photo' status isn't quite working (doesn't show at all)
    bot.send_chat_action(cid, 'typing')

    if text in lights:  # send the appropriate image based on the reply to the "/getImage" command
        b.set_light(text, 'on', m.stateRequest)
        bot.send_message(cid, 'Comando enviado', reply_markup=hideBoard)  # send file and hide keyboard, after image is sent
        userStep[cid] = 0  # reset the users step back to 0
    else:
        bot.send_message(cid, "¡No escribas tonterías si incluso te pongo un teclado con opciones en pantalla!")
        bot.send_message(cid, "Intenta de nuevo....")
    return

@bot.message_handler(func=lambda m: True, content_types=['text'])
def echo_all(message):
    print(message.text)
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')

    response = conversation.message(workspace_id=workspace_id, message_input={
        'text': message.text})
    try:
        if 'enciende' in response['intents'][0]['intent']:
            message.stateRequest = True
            cid = message.chat.id
            text = message.text

            if message.chat.id not in privilegedChats:
                bot.send_message(cid, "No tienes permiso, habla con Giuliano")
            else:
                lightsKeyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=False)  # create the image selection keyboard
                for item in getLights():
                    lightsKeyboard.add(item)
                    if item in text:
                        b.set_light(item, 'on', message.stateRequest)
                        bot.send_message(cid, 'Listo')
                        return
                bot.send_message(cid, "¿Cual de todas?", reply_markup=lightsKeyboard)  # show the keyboard
                userStep[cid] = 1  # set the user to the next step (expecting a reply in the listener now)

        elif 'apaga' in response['intents'][0]['intent']:
            message.stateRequest = False
            cid = message.chat.id
            text = message.text

            if message.chat.id not in privilegedChats:
                bot.send_message(cid, "No tienes permiso, habla con Giuliano")
            else:
                lightsKeyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=False)  # create the image selection keyboard
                for item in getLights():
                    lightsKeyboard.add(item)
                    if item in text:
                        b.set_light(item, 'on', message.stateRequest)
                        bot.send_message(cid, 'Listo')
                        return
                bot.send_message(cid, "¿Cual de todas?", reply_markup=lightsKeyboard)  # show the keyboard
                userStep[cid] = 1  # set the user to the next step (expecting a reply in the listener now)

        elif 'hora' in response['intents'][0]['intent']:
            bot.reply_to(message, response['output']['text'][0].format(time.strftime('%H:%M:%S')))
        elif 'chiste' in response['intents'][0]['intent']:
            resp = requests.get('http://api.icndb.com/jokes/random')
            if resp.status_code != 200:
                bot.reply_to(message, response['output']['text'])
            else:
                joke = resp.json()['value']['joke'].replace('&quot;', '\"')
                translation = translator.translate(
                    text=joke,
                    source='en', target='es')
                bot.send_message(message.chat.id, translation)
        else:
            bot.send_message(message.chat.id, response['output']['text'], disable_notification=True)
    except(IndexError) as err:
        bot.reply_to(message, response['output']['text'])
        print(response)
        print(err)
    finally:
        pass

@bot.edited_message_handler(func=lambda m: True, content_types=['voice'])
def echo_voice(m):
    print(m)

bot.polling()