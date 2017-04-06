import telebot, requests, wolframalpha, persistence, sys, os, conversationTools
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
    lights = b.get_light_objects('name')
    for light in lights:
        yield light
    pass

privilegedChats = [42789923, 25863480]
def hasAccess(cid):
    if cid in privilegedChats:
        return True
    else:
        return False

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
tmp = []

commands = {  # command description used in the "help" command
                'help, /ayuda': 'Da informacion de los comandos disponibles.',
                'me, /yo': 'Muestra la información que el bot tiene sobre ti.',
                'ask, /pregunta, /preguntar'  : 'Pregúntale a un humano.',
                'ejemplos' : 'Muestra algunos ejemplos de preguntas interesantes.',
                'cid' : 'Muestra el chat id.',
                'reset': 'Permite reingresar tus datos básicos.',
}

adminCommands = {
    'broadcast' : 'Envía un mensaje masivo a todos los que han hablado con Watson.',
    'reply' : 'Responde un mensaje que haya sido enviado por un usuario mediante /ask. (Necesitas el chat id para responder)',
    'whois' : 'Obtiene fotos de perfil de una persona. (Necesitas el chat id)',
    'database' : 'Muestra la base de datos de usuarios y chat ids de Watson.'
}

ejemplos = ['Cuánta sal hay en el mar?', 'Puedes fallar el test de Turing?', 'Cuéntame un chiste sucio?', 'Two things are infinite...', 'Aeropuerto de santiago de chile', 'Quién dejó el gato afuera?', 'Tell me a physics joke', 'Iones de ácido débiles', 'Cálculo de gravedad', 'Próximo eclipse solar', 'Aplicaciones que soportan .gif', 'Pikachu', 'Voyager 1', 'Caninos', 'Lenguas de España']

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


@bot.message_handler(commands=['ask', 'pregunta', 'preguntar'])
def askGiuliano(message):
    cid = message.chat.id
    print ('{}: {}'.format(cid, message.text))
    bot.send_chat_action(cid, 'typing')
    bot.send_message(cid, database.user_dict[cid]['name'] + ', enviemos tu pregunta....\n¿Cual es tu pregunta?')
    userStep[cid] = 1
    bot.register_next_step_handler(message, sendQuestion)

def sendQuestion(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    print('{}: /ask {}'.format(cid, message.text))
    for item in privilegedChats:
        bot.forward_message(item, cid, message.message_id)
        bot.send_message(item, 'from: {}'.format(cid))
    bot.send_message(cid, 'Mensaje enviado, gracias. :)')

    userStep[cid] = 0

@bot.message_handler(commands=['reply'])
def replyQuestion(message):
    cid = message.chat.id
    print('{}: {}'.format(cid, message.text))
    bot.send_chat_action(cid, 'typing')
    if not hasAccess(cid):
        bot.send_message(cid, 'No tienes permiso.')
    else:
        bot.send_message(cid, 'Responder a: Respuesta')
        userStep[cid] = 1
        bot.register_next_step_handler(message, sendReply)

def sendReply(message):
    cid = message.chat.id
    print('{}: /reply {}'.format(cid, message.text))
    to = message.text.split(':')
    bot.forward_message(to, cid, message.message_id)
    bot.send_message(cid, 'Enviado')
    userStep[cid] = 0

@bot.message_handler(commands=['me', 'yo'])
def userInfo(message):
    cid = message.chat.id
    print('{}: {}'.format(cid, message.text))
    bot.send_chat_action(cid, 'typing')
    bot.send_message(cid, database.user_dict[cid]['name'] + ', esto es lo que sé de ti:\n- Edad: ' + str(
        database.user_dict[cid]['age']) + '\n- Sexo: ' + database.user_dict[cid]['sex'])

@bot.message_handler(commands=['cid'])
def userInfo(message):
    cid = message.chat.id
    print('{}: {}'.format(cid, message.text))
    bot.send_chat_action(cid, 'typing')
    bot.send_message(cid, cid)

@bot.message_handler(commands=['reset'])
def resetUser(message):
    cid = message.chat.id
    print('{}: {}'.format(cid, message.text))
    bot.send_chat_action(cid, 'typing')
    userStep[cid] = 1
    bot.send_message(cid, 'Vamos a verificar tu información!')
    bot.send_chat_action(cid, 'typing')
    time.sleep(1)
    userInfo(message)
    bot.send_message(cid, '¡Actualicemos la información!')
    bot.send_message(cid, '¿Cómo te llamas?')
    bot.register_next_step_handler(message, process_name_step)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    cid = message.chat.id
    print('{}: {}'.format(cid, message.text))
    if not hasAccess(cid):
        bot.send_message(cid, 'Lo siento, solo obedezco a Giuliano.')
        sendSystemBroadcast('{} intentó hacer broadcast por comando.'.format(cid))
    else:
        userStep[cid] = 1
        bot.send_message(cid, 'Broadcast:')
        bot.register_next_step_handler(message, getBroadcastMessage)

@bot.message_handler(commands=['database'])
def broadcast(message):
    cid = message.chat.id
    print('{}: {}'.format(cid, message.text))
    if not hasAccess(cid):
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
    print('{}: {}'.format(cid, message.text))
    bot.send_chat_action(cid, 'typing')
    if cid not in database.knownUsers:
        database.knownUsers.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
        print('{}: is new user'.format(cid))
        database.save
    if cid not in database.user_dict:  # if user hasn't used the "/start" command yet:
        bot.reply_to(message, 'Hola, soy Watson, un bot con machine learning, para aprender de mis interacciones con humanos.\nCuéntame un poco de ti :)')
        bot.send_message(cid, '¿Cuál es tu nombre?')
        bot.register_next_step_handler(message, process_name_step)
        userStep[cid] = 1
    else:
        bot.send_chat_action(cid, 'typing')
        response = conversation.message(workspace_id=workspace_id, message_input={
            'text': message.text, 'context' : cid})
        if response['output']['text'][0] not in ['askTwitter', 'askWolfram', 'sendWatson']:
            bot.reply_to(message, response['output']['text'])
        else:
            bot.send_message(cid, "¿Qué me dijiste, lo puedes repetir?", disable_notification=True)
    return



def process_name_step(message):
    try:
        chat_id = message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        name = message.text
        database.user_dict[chat_id] = {}
        database.user_dict[chat_id]['name'] = name
        database.user_dict[chat_id]['id'] = message.from_user.id
        msg = bot.reply_to(message, '¿Cuántos años tienes?\nPor favor responde solo con números.')
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
        markup.add('Hombre', 'Mujer')
        msg = bot.reply_to(message, '¿Cuál es tu género?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_sex_step)
    except Exception as e:
        bot.reply_to(message, 'oooops {}'.format(e))

def process_sex_step(message):
    try:
        chat_id = message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        sex = message.text
        if (sex == u'Hombre') or (sex == u'Mujer'):
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
    print('{}: {}'.format(cid, m.text))
    sendSystemBroadcast('{} trató de matar a todo el mundo.'.format(cid))
    bot.send_message(cid, 'Hay un error de autorización para eso.')  # send the generated help page

@bot.message_handler(commands=['whois'])
def whois(message):
    cid = message.chat.id
    if not hasAccess(cid):
        bot.send_message(cid, 'Lo siento, solo obedezco a Giuliano.')
        sendSystemBroadcast('{} intentó obtener info de un usuario por comando.'.format(cid))
    else:
        userStep[cid] = 1
        bot.send_message(cid, 'cid:')
        bot.register_next_step_handler(message, getUserInfo)

def getUserInfo(message):
    cid = message.chat.id
    try:
        photo = bot.get_user_profile_photos(database.user_dict[int(message.text)]['id'], limit=2)
        if len(photo.photos) == 0: return bot.send_message(cid, 'No hay fotos para \'{}\' :('.format(database.user_dict[int(message.text)]['name']))
        for item in photo.photos:
            bot.send_chat_action(cid, 'upload_photo')
            fid = item[0].file_id #File ID
            file_info = bot.get_file(fid) #Get file path by file ID
            downloaded_file = bot.download_file(file_info.file_path) #download file

            with open('./' + str(fid), 'wb') as new_file: #write file
                new_file.write(downloaded_file)
            new_file.close()

            photo = open('./' + fid, 'rb') #open reader
            bot.send_photo(42789923, photo, database.user_dict[int(message.text)]['name']) #send downloaded file
            photo.close()

            from os import remove
            remove('./' + str(fid)) #remove file

            userStep[cid] = 0

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        str = '{} {} {}'.format(exc_type, fname, exc_tb.tb_lineno)
        print(exc_type, fname, exc_tb.tb_lineno)
        sendSystemBroadcast('{} error >> {}'.format(cid, str))
        bot.reply_to(message, 'oooops {} >> {}'.format(e, str))

@bot.message_handler(commands=['help', 'h', 'ayuda'])
def command_help(m):
    cid = m.chat.id
    print('{}: {}'.format(cid, m.text))
    help_text = "Estos comandos podrían ser útiles: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page
    bot.send_message(cid, 'Si quieres saber más de mi o de las cosas que puedo hacer, solo debes preguntármelo.')

@bot.message_handler(commands=['ejemplos', 'ejemplo'])
def sendEjemplos(m):
    cid = m.chat.id
    print('{}: {}'.format(cid, m.text))
    examples = "Puedes decirme cosas como: \n"
    for item in ejemplos:
        examples += '\n- {}'.format(item)
    bot.send_message(cid, examples)  # send the generated help page
    bot.send_message(cid, 'Si quieres saber más de mi, solo debes preguntármelo.')

def offLight(message, bulb = None):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    if bulb == None: bulb = message.text
    try:
        if b.get_light(bulb)['state']['on'] == False:
            bot.send_message(cid, '[{}]: La luz ya estaba apagada.'.format(bulb))
        else:
            b.set_light(bulb, 'on', False)
            bot.send_chat_action(cid, 'typing')
            time.sleep(2)
            if b.get_light(bulb)['state']['on'] == False:
                bot.send_message(cid, 'Listo')
            else:
                bot.send_message(cid, '[{}]: Hubo un problema al apagar la luz.'.format(bulb))
                houseLightState(message)
        userStep[cid] = 0
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        str = '{} {} {}'.format(exc_type, fname, exc_tb.tb_lineno)
        print(exc_type, fname, exc_tb.tb_lineno)
        sendSystemBroadcast('{} error >> {}'.format(cid, str))
        bot.reply_to(message, 'oooops {} >> {}'.format(e, str))

def onLight(message, bulb = None):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    if bulb == None: bulb = message.text
    try:
        if b.get_light(bulb)['state']['on'] == True:
            bot.send_message(cid, '[{}]: La luz ya estaba encendida.'.format(bulb))
        else:
            bot.send_chat_action(cid, 'typing')
            time.sleep(2)
            b.set_light(bulb, 'on', True)
            if b.get_light(bulb)['state']['on'] == False:
                bot.send_message(cid, 'Listo')
            else:
                bot.send_message(cid, '[{}]: Hubo un problema al encender la luz.'.format(bulb))
                houseLightState(message)
        userStep[cid] = 0
    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        str = '{} {} {}'.format(exc_type, fname, exc_tb.tb_lineno)
        print(exc_type, fname, exc_tb.tb_lineno)
        sendSystemBroadcast('{} error >> {}'.format(cid, str))
        bot.reply_to(message, 'oooops {} >> {}'.format(e, str))

def houseLightState(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    mes = 'Este es el estado de la casa:\n'
    for item in getLights():
        mes += '[{}]: {}\n'.format(item, b.get_light(item)['state']['on'])
    mes = mes.replace('False', 'Apagada')
    mes = mes.replace('True', 'Encendida')
    bot.reply_to(message, mes)

@bot.message_handler(func=lambda m: get_user_step(m.chat.id, m) != 1, content_types=['text'])
def echo_all(message):
    cid = message.chat.id
    text = message.text
    bot.send_chat_action(cid, 'typing')

    response = conversation.message(workspace_id=workspace_id, message_input={
        'text': message.text, 'context' : cid})
    print('{}: {} >> R: {}'.format(cid, message.text, response['output']['text'][0]))
    try:
        if conversationTools.hasIntent(response, 'enciende'):
            message.stateRequest = False
            cid = message.chat.id
            text = message.text

            if not hasAccess(message.chat.id):
                bot.send_message(cid, "No tienes permiso.")
                return
            else:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for item in getLights():
                    markup.add(item)
                    if item in text:
                        bot.send_message(message.chat.id, response['output']['text'], disable_notification=True)
                        onLight(message, item)
                        return
                bot.send_message(cid, "¿Cuál de todas?", reply_markup=markup)  # show the keyboard
                userStep[cid] = 1
                bot.register_next_step_handler(message, onLight)

        elif conversationTools.hasIntent(response, 'apaga'):
            message.stateRequest = False
            cid = message.chat.id
            text = message.text

            if not hasAccess(message.chat.id):
                bot.send_message(cid, "No tienes permiso.")
                return
            else:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for item in getLights():
                    markup.add(item)
                    if item in text:
                        bot.send_message(message.chat.id, response['output']['text'], disable_notification=True)
                        offLight(message, item)
                        return
                bot.send_message(cid, "¿Cuál de todas?", reply_markup=markup)  # show the keyboard
                userStep[cid] = 1
                bot.register_next_step_handler(message, offLight)
                bot.send_message(message.chat.id, response['output']['text'], disable_notification=True)

        elif conversationTools.hasIntent(response, 'lista_luces'):
            cid = message.chat.id
            if not hasAccess(message.chat.id):
                bot.send_message(cid, "No tienes permiso, habla con Giuliano")
                return
            bot.send_message(message.chat.id, response['output']['text'], disable_notification=True)
            bot.send_chat_action(cid, 'typing')

            lightList = ''
            i = 0
            for item in getLights():
                if i == 0:
                    lightList += item
                else:
                    lightList += ', {}'.format(item)
                i += 1
            bot.send_message(cid, 'Estas son las luces que encontré: {}'.format(lightList))

        elif conversationTools.hasResponseText(response, 'sendWatson'):
            from random import randint
            photo = open('./img/' + str(randint(1, 2))+'.jpg', 'rb')  # open reader
            bot.send_chat_action(cid, 'upload_photo')
            bot.send_photo(cid, photo, 'THINK')  # send downloaded file

        elif conversationTools.hasResponseText(response, 'askWolfram'):
            handleWolframQuestion(message)

        elif conversationTools.hasIntent(response, 'hora'):
            bot.reply_to(message, response['output']['text'][0].format(time.strftime('%H:%M:%S')))
        elif conversationTools.hasIntent(response, 'estadoCasa'):
            bot.send_chat_action(cid, 'typing')
            bot.send_message(cid, response['output']['text'][0])
            bot.send_chat_action(cid, 'typing')
            houseLightState(message)
            return
        elif conversationTools.hasIntent(response, 'chiste'):
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
            bot.send_message(message.chat.id, response['output']['text'][0])
            if conversationTools.isEmpty(response):
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Si', 'No')
                bot.send_message(cid, '¿Busco información adicional?', reply_markup=markup)
                tmp.append(message)
                userStep[cid] = 1
                message = bot.register_next_step_handler(message, askWolfram)

    except(IndexError) as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        str = '{} {} {}'.format(exc_type, fname, exc_tb.tb_lineno)
        print(exc_type, fname, exc_tb.tb_lineno)
        sendSystemBroadcast('{} error >> {}'.format(cid, str))
        bot.reply_to(message, 'oooops {} >> {}: {}'.format(e, response['output']['text'][0], str))

    finally:
        pass

def askWolfram(message):
    cid = message.chat.id
    selection = message.text
    try:
        if (selection == u'Si'):
            userStep[cid] = 0
            handleWolframQuestion(tmp[0])
            tmp.clear()
            return 1
        else:
            userStep[cid] = 0
            return 0
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops {}'.format(e))

def handleWolframQuestion(message):
    cid = message.chat.id
    text = message.text
    inputTranslation = translator.translate(text=text, source='es', target='en')
    bot.send_chat_action(cid, 'upload_document')
    res = wolfram.query(inputTranslation)

    if res.success == 'false':
        bot.send_message(cid, 'Estoy pensando.....', disable_notification=True)
        bot.send_chat_action(cid, 'upload_document')
        try:
            res = wolfram.query(res.didyoumeans['didyoumean']['#text'])
        except(TypeError):
            bot.reply_to(message, 'No puedo responder esto, le pregunté a otro bot y tampoco sabe :(')

    if hasattr(res, 'results'):
        for pod in res.results:
            if hasattr(pod, 'subpod'):
                for subpod in pod.subpod:
                    if hasattr(subpod, 'plaintext'):
                        bot.send_chat_action(cid, 'typing')
                        bot.reply_to(message, subpod['plaintext'])

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