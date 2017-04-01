import telebot, requests, wolframalpha, persistence, sys
from telebot import types
from watson_developer_cloud import ConversationV1, LanguageTranslatorV2
import time
from phue import Bridge

b = Bridge('172.27.0.116')
b.connect()

databaseFile = 'pyping-v1.db'
databasePath = './' + databaseFile

database = persistence.Database(databasePath)

def getLights():
#    lights = b.get_light_objects('name')
#    for light in lights:
#        yield light
    pass

bot = telebot.TeleBot("352103827:AAG1fNzI5S3M_Xg0B5cnhFKP3w6NwJHxi24")
conversation = ConversationV1(
    username='de3f5464-f9da-46e0-b517-203d4e95237c',
    password='fwvhVMKSFyP0',
    version='2017-03-28')
workspace_id = 'edbf9f5c-938b-4470-b3fd-24b42efed20a'

translator = LanguageTranslatorV2(
   username='3fac851e-8f83-4b59-b62a-1494a79aef86',
   password='2krMxrkYIBkS')

wolfram = wolframalpha.Client('VHE2HT-4VQW535Y3X')


userStep = {}  # so they won't reset every time the bot restarts

privilegedChats = [42789923]

commands = {  # command description used in the "help" command
                'start': 'Usar el bot',
                'help': 'Da informacion de los comandos disponibles.',
                'me': 'Muestra la información que el bot tiene sobre ti.',
                'reset': 'Permite reingresar tus datos básicos.',
}

hideBoard = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard

# error handling if user isn't known yet
# (obsolete once known users are saved to file, because all users
#   had to use the /start command and are therefore known to the bot)
def get_user_step(uid, message):
    if uid in userStep:
        return userStep[uid]
    else:
        userStep[uid] = 0
        send_welcome(message)
        return 1

@bot.message_handler(commands=['me'])
def userInfo(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    bot.send_message(cid, database.user_dict[cid]['name'] + ', esto es lo que sé de ti:\n- Edad: ' + str(
        database.user_dict[cid]['age']) + '\n- Sexo: ' + database.user_dict[cid]['sex'])

@bot.message_handler(commands=['reset'])
def resetUser(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    userStep[cid] = 1
    bot.send_message(cid, 'Vamos a verificar tu información!')
    bot.send_chat_action(cid, 'typing')
    time.sleep(2)
    userInfo(message)
    bot.send_message(cid, '¡Actualicemos la información!')
    bot.send_message(cid, '¿Cómo te llamas?')
    bot.register_next_step_handler(message, process_name_step)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    cid = message.chat.id
    if cid not in privilegedChats:
        bot.send_message(cid, 'Lo siento, solo obedezco a Giuliano.')
        sendSystemBroadcast('{} intentó hacer broadcast por comando.'.format(cid))
    else:
        userStep[cid] = 1
        bot.send_message(cid, 'Broadcast:')
        bot.register_next_step_handler(message, getBroadcastMessage)

@bot.message_handler(commands=['database'])
def broadcast(message):
    cid = message.chat.id
    if cid not in privilegedChats:
        bot.send_message(cid, 'Lo siento, solo obedezco a Giuliano.')
        sendSystemBroadcast('{} intentó acceder a la base de datos por comando.'.format(cid))
    else:
        bot.send_message(cid, database)

def getBroadcastMessage(message):
    cid = message.chat.id
    userStep[cid] = 0
    for chat in database.knownUsers:
        bot.send_message(chat, message.text)

def sendSystemBroadcast(messageString):
    for chat in privilegedChats:
        bot.send_message(chat, messageString)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    if cid not in database.knownUsers:
        database.knownUsers.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
        print('{}: is new user'.format(cid))
        database.save
    if cid not in database.user_dict:  # if user hasn't used the "/start" command yet:
        bot.reply_to(message, 'Hola, soy Watson, un bot con principios de machine learning, lo cual me ayuda a aprender de mis interacciones con humanos.\nCuéntame un poco de ti :)')
        bot.send_message(cid, '¿Cuál es tu nombre?')
        bot.register_next_step_handler(message, process_name_step)
        userStep[cid] = 1
    else:
        bot.send_message(cid, "Hola {}, ya estamos conectados!".format(database.user_dict[cid]['name']))


def process_name_step(message):
    try:
        chat_id = message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        name = message.text
        database.user_dict[chat_id] = {}
        database.user_dict[chat_id]['name'] = name
        database.user_dict[chat_id]['id'] = message.from_user.id
        msg = bot.reply_to(message, '¿Cuántos años tienes?')
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        bot.reply_to(message, 'oooops {}'.format(e))

def process_age_step(message):
    try:
        chat_id = message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        age = message.text
        if not age.isdigit():
            msg = bot.reply_to(message, 'Hey, no me engañes! ¿Cuántos años tienes?')
            sendSystemBroadcast('{} no quiere dar su edad.\n>> {}'.format(chat_id, age))
            bot.register_next_step_handler(msg, process_age_step)
            return
        database.user_dict[chat_id]['age'] = age
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Macho', 'Hembra')
        msg = bot.reply_to(message, '¿Cuál es tu género?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_sex_step)
    except Exception as e:
        bot.reply_to(message, 'oooops {}'.format(e))

def process_sex_step(message):
    try:
        chat_id = message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        sex = message.text
        if (sex == u'Macho') or (sex == u'Hembra'):
            database.user_dict[chat_id]['sex'] = sex
        else:
            raise Exception()
        bot.send_message(chat_id, 'Gusto en conocerte, ' + database.user_dict[chat_id]['name'] + '\n Edad:' + str(database.user_dict[chat_id]['age']) + '\n Sexo:' + database.user_dict[chat_id]['sex'])
        database.refresh()
        userStep[chat_id] = 0
        command_help(message)  # show the new user the help page
    except Exception as e:
        bot.reply_to(message, 'oooops {}'.format(e))

@bot.message_handler(commands=['kill'])
def kill(m):
    cid = m.chat.id
    sendSystemBroadcast('{} trató de matar a todo el mundo.'.format(cid))
    bot.send_message(cid, 'Hay un error de autorización para eso.')  # send the generated help page

@bot.message_handler(commands=['whois'])
def whois(message):
    cid = message.chat.id
    if cid not in privilegedChats:
        bot.send_message(cid, 'Lo siento, solo obedezco a Giuliano.')
        sendSystemBroadcast('{} intentó obtener info de un usuario por comando.'.format(cid))
    else:
        userStep[cid] = 1
        bot.send_message(cid, 'cid:')
        bot.register_next_step_handler(message, getUserInfo)

def getUserInfo(message):
    try:
        photo = bot.get_user_profile_photos(database.user_dict[int(message.text)]['id'], limit=2)
        for item in photo.photos:
            fid = item[0].file_id #File ID
            file_info = bot.get_file(fid) #Get file path by file ID
            downloaded_file = bot.download_file(file_info.file_path) #download file

            with open('./' + str(fid), 'wb') as new_file: #write file
                new_file.write(downloaded_file)
            new_file.close()

            photo = open('./' + fid, 'rb') #open reader
            bot.send_photo(42789923, photo, database.user_dict[int(message.text)]['name']) #send downloaded file

            from os import remove
            remove('./' + str(fid)) #remove file

    except Exception as e:
        bot.reply_to(message, 'oooops {}'.format(e))


@bot.message_handler(commands=['help', 'h'])
def command_help(m):
    cid = m.chat.id
    help_text = "Estos comandos podrían ser útiles: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page
    bot.send_message(cid, 'Si quieres saber más de mi o de las cosas que puedo hacer, solo debes preguntármelo.')

# @bot.message_handler(func=lambda message: get_user_step(message.chat.id, message) == 1)
# def lightSelection(m):
#     cid = m.chat.id
#     text = m.text
#     lights = []
#
# #    for item in getLights():
# #        lights.append(item)
#
#     # for some reason the 'upload_photo' status isn't quite working (doesn't show at all)
#     bot.send_chat_action(cid, 'typing')
#
#     if text in lights:  # send the appropriate image based on the reply to the "/getImage" command
#         b.set_light(text, 'on', 'True')
#         bot.send_message(cid, 'Comando enviado', reply_markup=hideBoard)  # send file and hide keyboard, after image is sent
#         userStep[cid] = 0  # reset the users step back to 0
#     else:
#         bot.send_message(cid, "¡No escribas tonterías si incluso te pongo un teclado con opciones en pantalla!")
#         bot.send_message(cid, "Intenta de nuevo....")
#     return

@bot.message_handler(func=lambda m: get_user_step(m.chat.id, m) != 1, content_types=['text'])
def echo_all(message):
    cid = message.chat.id
    text = message.text
    bot.send_chat_action(cid, 'typing')

    response = conversation.message(workspace_id=workspace_id, message_input={
        'text': message.text})
    print('{}: {} >> R: {}'.format(cid, message.text, response['output']['text'][0]))
    try:
        if 'enciende' in response['intents'][0]['intent']:
            message.stateRequest = True

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

        elif 'lista_luces' in response['intents'][0]['intent']:
            cid = message.chat.id
            bot.send_message(message.chat.id, response['output']['text'], disable_notification=True)
            bot.send_chat_action(cid, 'typing')

            if message.chat.id not in privilegedChats:
                bot.send_message(cid, "No tienes permiso, habla con Giuliano")

            lightList = ''
            i = 0
            for item in getLights():
                if i == 0:
                    lightList += item
                else:
                    lightList += ', {}'.format(item)
                i += 1
            bot.send_message(cid, 'Estas son las luces que encontré: {}'.format(lightList))

        elif response['output']['text'][0] == 'sendWatson':
            from random import randint
            photo = open('./img/' + randint(1, 2), 'rb')  # open reader
            bot.send_photo(42789923, photo, 'THINK')  # send downloaded file

        elif response['output']['text'][0] == 'AskWolfram':
            inputTranslation = translator.translate(text=text, source='es', target='en')
            bot.send_message(cid, 'hablando con WolframAlpha...')
            bot.send_message(cid, 'Wolfram query>> {}'.format(inputTranslation))
            res = wolfram.query(inputTranslation)
            if res.success == 'false':
                print('hola')
                bot.send_message(cid, 'Wolfram >> FAIL')
                bot.send_message(cid, 'Estoy pensando.....', disable_notification=True)
                bot.send_chat_action(cid, 'typing')
                res = wolfram.query(res.didyoumeans['didyoumean']['#text'])
                bot.send_message(cid, 'maybe >> {} >> query'.format(res.didyoumeans['didyoumean']['#text']), disable_notification=True)
            try:
                print('chao')
                bot.send_message(cid, 'Wolfram result>> {}'.format(next(res.results)))
                #for item in res.results:
                #    print(item)
                #    hasattr(item, 'text')
                #for item in res.pods:
                #    if hasattr(item, 'subpod'):
                #        for subpod in item:
                #            print(type(getattr(item, subpod)))
                #            print('{} >> {}'.format(subpod, getattr(item, subpod)))
                #for pod in res.pods:
                    #if hasattr(pod, 'primary') and hasattr(pod, 'results'):
                    #    print('Primario!!!!')
                    #    print(pod)
                #bot.reply_to(message, translator.translate(text=next(res.results).text, source='en', target='es'))
            except(StopIteration):
                print(next(res.results).text)
                bot.send_message(cid, 'Tu pregunta es muy amplia y tiene demasiadas respuestas :(', disable_notification=False)


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
        bot.reply_to(message, 'FAIL >> {} >> R: {}'.format(err, response['output']['text'][0]))
        print(response)
        print(err)
    finally:
        pass

@bot.edited_message_handler(func=lambda m: True, content_types=['voice'])
def echo_voice(m):
    print(m)




def main_loop():
    bot.polling(True)
    while 1:
        time.sleep(1)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)