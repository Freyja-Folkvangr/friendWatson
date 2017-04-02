def hasIntent(response, intent):
    if 'intents' in response:
            if intent in response['intents']:
                return True
    return False

def hasEntity(response, text):
    pass

def hasResponseText(response, text):
    if 'output' in response:
        if 'text' in response['output']:
            if text in response['output']['text']:
                return True
    return False