# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 10:06:18 2022

@author: afisher
"""

import os
import time
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import pandas as pd
import numpy as np
import pickle
import datetime
from ELO import ELO
from Handler import Handler

# Tokens
SLACK_BOT_TOKEN = os.environ['FOOSBOT_BOT_TOKEN']
SLACK_BOT_USER_TOKEN = os.environ['FOOSBOT_BOT_USER_TOKEN']
app = App(token=SLACK_BOT_TOKEN)

HANDLER = Handler(app, SLACK_BOT_TOKEN, SLACK_BOT_USER_TOKEN)

@app.event("app_mention")
def handle_app_mention_events(event, say, ack):
    HANDLER.handle_app_mention_events(event, say, ack)

@app.action("submit_game-action")
def handle_game_submission(ack, body, logger):
    HANDLER.handle_game_submission(ack, body, logger)
    
@app.action("cancel_message")
def handle_cancellation(ack, body, logger):
    HANDLER.handle_cancellation(ack, body, logger)
    


# Dummy events
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)
    
@app.action("static_select-action")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    
if __name__=="__main__":
    SocketModeHandler(app, SLACK_BOT_TOKEN).start()