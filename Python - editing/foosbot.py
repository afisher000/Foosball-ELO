# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 10:06:18 2022

@author: afisher
"""

import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import utils_bot as ub
import ELO
from datetime import datetime
# from Handler import Handler

IN_TESTING = False


if IN_TESTING:
    # Tokens for testing/development in BotTesting 
    SLACK_BOT_TOKEN = os.environ['FOOSBOT_BOT_TOKEN']
    SLACK_BOT_USER_TOKEN = os.environ['FOOSBOT_BOT_USER_TOKEN']
    foosball_channel = 'C04H21NAM44'
    andy_user = 'U041KR1G9TJ'
else:
    # Tokens for deployment in Pegasuslab
    SLACK_BOT_TOKEN = os.environ['PBPL_FOOSBOT_TOKEN']
    SLACK_BOT_USER_TOKEN = os.environ['PBPL_FOOSBOT_USER_TOKEN']
    foosball_channel = 'C042YTYSDJ5'
    andy_user = 'W01A1T44K2B'

app = App(token=SLACK_BOT_USER_TOKEN)
ELO.rebuild_rating_db()


@app.event("message")
def handle_message_events(event, say, ack):
    ack()
    # Do not respond to bot messages
    if 'user' not in event.keys() or event['user']==SLACK_BOT_USER_TOKEN:
        return

    # Only respond to andrew messages when testing
    if IN_TESTING and event['user']!=andy_user:
        return
    
    # Call utils_bot functions 
    function, argument = ub.parse_slackbot_call(event['text'])
    if function in ub.function_scopes.keys():
        if event['channel'][0] in ub.function_scopes[function]:
            post_object = getattr(ub, 'function_'+function)(argument)
            
            if 'image_file' in post_object.keys():
                upload_image(event, **post_object)
            else:
                say(token=SLACK_BOT_USER_TOKEN, **post_object)
                
        else:
            say(
                token = SLACK_BOT_USER_TOKEN, 
                text='Channel not included in function scope. See help()'
            )
    else:
        say( 
            token = SLACK_BOT_USER_TOKEN,
            text = (
                'Cound not parse message, remember to use the format "function(argument)".\n'
                'Try "help()" for suggestions.'
            )
        )
    
    
@app.action("delete_game-action")
def handle_game_deletion(say, ack, body, logger):
    ack()
    index = body['state']['values']['idx_id']['static_select-action']['selected_option']['value']
    ELO.delete_game_by_index(int(index))
    
    # Cancel message and send confirmation
    app.client.chat_delete( 
        token = SLACK_BOT_USER_TOKEN,
        channel = body['channel']['id'],
        ts = body['message']['ts'],
        blocks = None)
    say(
        token = SLACK_BOT_USER_TOKEN, 
        text='Game deleted successfully and ratings recalculated'
    )
    return



@app.action("submit_game-action")
def handle_game_submission(say, ack, body, logger):
    ack()
    # Read selections
    try:
        WO = body['state']['values']['WO_id']['static_select-action']['selected_option']['value']
        WD = body['state']['values']['WD_id']['static_select-action']['selected_option']['value']
        LO = body['state']['values']['LO_id']['static_select-action']['selected_option']['value']
        LD = body['state']['values']['LD_id']['static_select-action']['selected_option']['value']
        color = body['state']['values']['color_id']['static_select-action']['selected_option']['value']
        score = body['state']['values']['score_id']['static_select-action']['selected_option']['value']
        date = datetime.today().strftime('%m/%d/%Y')
    except:
        app.client.chat_postMessage(
            token = SLACK_BOT_USER_TOKEN, 
            channel = body['channel']['id'],
            text = 'Selection incomplete'
        )
        return
    
    # Post confirmation and delete menus
    post_object = ub.submit_game(WO, WD, LO, LD, score, date, color)
    say(token = SLACK_BOT_USER_TOKEN, **post_object)
    app.client.chat_delete( 
        token = SLACK_BOT_USER_TOKEN,
        channel = body['channel']['id'],
        ts = body['message']['ts'],
        blocks=None
    )


    
@app.action("cancel_message")
def handle_cancellation(ack, body, logger):
    ack()
    app.client.chat_delete( 
        token = SLACK_BOT_USER_TOKEN,
        channel = body['channel']['id'],
        ts = body['message']['ts'],
        blocks = None)
    return
    
    
def upload_image(event, image_file, text):
    app.client.files_upload(
        token = SLACK_BOT_USER_TOKEN,
        file = image_file,
        channels = event['channel'], 
        initial_comment = text
    )
    return
    
# Dummy events
@app.action("static_select-action")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    
if __name__=="__main__":
    SocketModeHandler(app, SLACK_BOT_TOKEN).start()
    