def hasIntent(response, intent):
    if 'intents' in response and not isEmpty(response):
        if intent in response['intents'][0]['intent']:
            return True
    return False

def isEmpty(response):
    if 'intents' in response:
        return not len(response['intents'])
    return False

def hasEntity(response, text):
    pass

def hasResponseText(response, text):
    if 'output' in response:
        if 'text' in response['output']:
            if text in response['output']['text']:
                return True
    return False