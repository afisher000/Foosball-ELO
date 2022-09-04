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


# Tokens (export to environment variable in future)
SLACK_BOT_TOKEN = 'xapp-1-A041BLUJ1C1-4032980761635-3f1feaa3bb3774828420536a2ac8c21d636ae5279a69e216aac9e53d4caa53bf'
SLACK_BOT_USER_TOKEN = 'xoxb-4030047472195-4035541061012-ShTpBM2Uo5QXzEIU4l4GNI8w'
app = App(token=SLACK_BOT_TOKEN)

# Load initial data
elo = ELO('Game Log.csv', k=64, spread=200)
elo.simulate()
players = (elo.gamelog[['WO','WD','LO','LD']]
           .apply(pd.Series.value_counts)
           .sum(axis=1)
           .sort_values(ascending=False).index)
ratings = elo.get_ratings()


def options_dict(items):
    return [{'text':{'type':'plain_text', 'text':item}, 'value':item} 
            for item in items] 


def static_select_block(id_, text, items):
    block = {'type':'section',
             'block_id':id_,
             'text':{'type':'mrkdwn',
                     'text':text},
             'accessory':{'type':'static_select',
                          'placeholder':{'type':'plain_text',
                                         'text':'Select an item'},
                          'options':options_dict(items),
                          'action_id':'static_select-action'
                          }
             }
    
    return block

def button_block(id_, text):
    block = {'type':'actions',
             'elements':[{'type':'button',
                          'text':{'type':'plain_text',
                                  'text':text},
                          'value':'submit',
                          'action_id':id_
                          }]
             }

    return block

def text_block(text):
    block = {'type':'section',
             'text':{'type':'mrkdwn',
                     'text':text}
             }
    return block


def new_game_block(players):
    blocks = [static_select_block('WO_id', 'Winner Offense', players),
              static_select_block('WD_id', 'Winner Defense', players),
              static_select_block('LO_id', 'Loser Offense', players),
              static_select_block('LD_id', 'Loser Defense', players),
              static_select_block('color_id', 'Winner Color', ['red','blue']),
              static_select_block('score_id', 'Score', list(map(str, range(10)))),
               button_block('button_id', 'Submit')
              ] 
    return blocks


@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)


@app.action("static_select-action")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    
@app.action("button_id")
def add_game(ack, body, logger):
    ack()
    ts = body['message']['ts']
    channel_id = body['channel']['id']
    
    # Read selections
    try:
        WO = body['state']['values']['WO_id']['static_select-action']['selected_option']['value']
        WD = body['state']['values']['WD_id']['static_select-action']['selected_option']['value']
        LO = body['state']['values']['LO_id']['static_select-action']['selected_option']['value']
        LD = body['state']['values']['LD_id']['static_select-action']['selected_option']['value']
        color = body['state']['values']['color_id']['static_select-action']['selected_option']['value']
        score = body['state']['values']['score_id']['static_select-action']['selected_option']['value']
    except:
        app.client.chat_postMessage(token=SLACK_BOT_USER_TOKEN, 
                                    channel=channel_id,
                                    text='Selection incomplete...')
        return
    
    if len(np.unique([WO, WD, LO, LD]))<4:
        app.client.chat_postMessage(token=SLACK_BOT_USER_TOKEN, 
                                    channel=channel_id,
                                    text='Duplicate player...')
        return
        
    
    # Add to gamelog and save
    elo.gamelog.loc[len(elo.gamelog)] = [WO, WD, LO, LD, int(score), 
                                 datetime.date.today(), color[0]]
    temp = elo.gamelog.copy()
    temp.Date = temp.Date.map(lambda x: x.strftime('%m/%d/%Y'))
    temp.to_csv('Game Log.csv', index=False)
    
    # Compute update ratings
    spread = 200
    k = 64
    W_rating = ratings[WO+'_off']/2 + ratings[WD+'_def']/2
    L_rating = ratings[LO+'_off']/2 + ratings[LD+'_def']/2
    actual_win_ratio = 10/(int(score)+10)
    expected_win_ratio = (1+10**((L_rating-W_rating)/elo.spread))**(-1)
    rating_change = elo.k * (actual_win_ratio - expected_win_ratio)
    if rating_change>0:
        bot_message = f'Added game to database. Winners gain {rating_change:.1f} rating'
    else:
        bot_message = f'Added game to database. Losers gain {-rating_change:.1f} rating'
    
    ratings[WO+'_off'] += rating_change
    ratings[WD+'_def'] += rating_change
    ratings[LO+'_off'] -= rating_change
    ratings[LD+'_def'] -= rating_change
    
    # Update message
    updated_message = f'Added game to database'
    app.client.chat_delete(token=SLACK_BOT_USER_TOKEN,
                           channel=channel_id, 
                           ts=ts,
                           blocks=None)
    app.client.chat_postMessage(token=SLACK_BOT_USER_TOKEN, 
                                channel=channel_id,
                                text=bot_message)
        
    
    pickle.dump(body, open('body.pkl','wb'))
    logger.info(body)
    
    
@app.event("app_mention")
def handle_mentions(event, say, ack):
    global players
    # Acknowledge connection with slack
    ack()
    
    # Parse input
    regex = re.compile('(<[^>]*>)([\w\s]*)\((\w*)\)')
    try:
        groups = regex.search(event['text']).groups()
        mention, keyword, arg = [group.strip() for group in groups]
    except:
        say(token=SLACK_BOT_USER_TOKEN, 
            text = 'Can not parse input.')
        keyword = 'help'
    
    
    
    # Switch structure
    if keyword=='newgame':
        app.client.chat_postMessage(
            token=SLACK_BOT_USER_TOKEN,
            channel=event['channel'],
            text = 'Add game information',
            blocks = new_game_block(players)
            )
        
    elif keyword=='newplayer':
        players = np.append(players, arg)
        say(token=SLACK_BOT_USER_TOKEN, text=f'Added new player "{arg}"')
        
    elif keyword=='help':
        say(token=SLACK_BOT_USER_TOKEN, 
            text='''The following are possible commands:
                @foosbot newgame()
                @foosbot newplayer(new_player_name)
                @foosbot ratings()''')
        
    elif keyword=='ratings':
        cutoff_date = datetime.datetime.today() - datetime.timedelta(30)
        cur_players = np.unique(elo.gamelog[elo.gamelog.Date>cutoff_date][['WO','WD','LO','LD']])
        rating_table = pd.DataFrame(index=cur_players)
        rating_table['Offense'] = ratings[cur_players+'_off'].values
        rating_table['Defense'] = ratings[cur_players+'_def'].values
        rating_table['Total'] = rating_table.Offense/2 + rating_table.Defense/2
        rating_table.sort_values(by='Total', ascending=False, inplace=True)
        rating_table[['Offense','Defense','Total']] = rating_table[['Offense','Defense','Total']].applymap(lambda x: f'{x:6.0f}')

        app.client.chat_postMessage(token=SLACK_BOT_USER_TOKEN,
                                    channel=event['channel'],
                                    text='Ratings',
                                    blocks = [{'type':'section',
                                              'text':{'type':'mrkdwn',
                                                      'text':"```"+ str(rating_table) +"```"}
                                              }])
        
        
        
        
        
        
if __name__=="__main__":
    SocketModeHandler(app, SLACK_BOT_TOKEN).start()