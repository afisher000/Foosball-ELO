# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 11:52:55 2022

@author: afish
"""

def option_object(item):
    return {'text':{'type':'plain_text', 'text':str(item)}, 'value':str(item)} 
    
def options_dict(items):
    return [option_object(item) for item in items]

def plain_text_input(block_id, label, action_id):
    block = {'type':'input',
             'block_id':block_id,
             'element':{'type':'plain_text_input',
                        'action_id':action_id},
             'label':{'type':'plain_text',
                      'text':label}
             }

    return block
    
    
def plain_text(text):
    block = {'type':'context',
             'elements':[{'type':'plain_text',
                          'text':text}]
             }
    return block

def actions(*args):
    elements = [arg for arg in args]
    block = {'type':'actions',
             'elements':elements}
    return block

def static_select(block_id, text, items, 
                  action_id='static_select-action',
                  placeholder_text='Select an item',
                  initial_option=None):
    block = {'type':'section',
             'block_id':block_id,
             'text':{'type':'mrkdwn',
                     'text':text},
             'accessory':{'type':'static_select',
                          'placeholder':{'type':'plain_text',
                                         'text':placeholder_text},
                          'options':options_dict(items),
                          'action_id':action_id
                          }
             }
    
    if initial_option is not None:
        block['accessory']['initial_option'] = initial_option
        
    return block

def button(block_id, label, button_text, action_id='button-action'):
    block = {'type':'section',
             'block_id':block_id,
             'text':{'type':'mrkdwn',
                     'text':label},
             'accessory':{'type':'button',
                          'text':{'type':'plain_text',
                                  'text':button_text},
                          'value':'default',
                          'action_id':action_id}
             }

    return block

def markdown(text):
    block = {'type':'section',
             'text':{'type':'mrkdwn',
                     'text':"```"+text+"```"}
             }
    return block