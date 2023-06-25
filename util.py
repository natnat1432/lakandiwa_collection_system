import requests
import random
from datetime import time
from decimal import Decimal
import json

def getQuotes():
    url = "https://type.fit/api/quotes"
    response = requests.get(url)

    data = response.json()
    rand_num = random.randint(0,len(data)-1)
    return data[rand_num]

def formatTime(rendered_hours):
    hours = rendered_hours.seconds // 3600
    minutes = (rendered_hours.seconds % 3600) // 60
    seconds = rendered_hours.seconds % 60
    return time(hours,minutes,seconds)

def is_table_empty(table):
    query = table.query.first()
    if query:
        return False
    else:
        return True
    

# Custom JSON encoder class
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)
    