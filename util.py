import requests
import random
from datetime import time,datetime
from decimal import Decimal
import json
import re

def getQuotes():
    url = "https://type.fit/api/quotes"
    response = requests.get(url)

    data = response.json()
    rand_num = random.randint(0,len(data)-1)
    return data[rand_num]

def formatTime(rendered_hours):
    if rendered_hours is not None:
        hours = rendered_hours.seconds // 3600
        minutes = (rendered_hours.seconds % 3600) // 60
        seconds = rendered_hours.seconds % 60
        return time(hours, minutes, seconds)
    else:
        return None

def is_table_empty(table):
    query = table.query.first()
    if query:
        return False
    else:
        return True
    
def toDateTime(date:str):
    return datetime.strptime(date,'%Y-%m-%dT%H:%M')


def getnametodict(name):
    # Pattern 1: lastname, firstname mi.
    pattern1 = r'^(?P<lastname>[A-Za-z\sñÑ\u010D\u010D-]+),\s(?P<firstname>[A-Za-z\sñÑ\u010D\u010D-]+)(?:\s(?P<middlename>[A-Za-z\sñÑ\u010D\u010D])\.)?$'
    match1 = re.match(pattern1, name)
    if match1:
        groups = match1.groupdict()
        return {
            'firstname': groups['firstname'].strip(),
            'lastname': groups['lastname'].strip(),
            'middlename': groups['middlename']
        }

    # Pattern 2: firstname mi. lastname
    pattern2 = r'^(?P<firstname>[A-Za-z\sñÑ\u010D\u010D-]+)\s(?P<middlename>[A-Za-z\sñÑ\u010D\u010D])\.\s(?P<lastname>[A-Za-z\sñÑ\u010D\u010D-]+)$'
    match2 = re.match(pattern2, name)
    if match2:
        groups = match2.groupdict()
        return {
            'firstname': groups['firstname'].strip(),
            'lastname': groups['lastname'].strip(),
            'middlename': groups['middlename']
        }

    # Pattern 3: lastname, firstname
    pattern3 = r'^(?P<lastname>[A-Za-z\sñÑ\u010D\u010D-]+),\s(?P<firstname>[A-Za-z\sñÑ\u010D\u010D-]+)$'
    match3 = re.match(pattern3, name)
    if match3:
        groups = match3.groupdict()
        return {
            'firstname': groups['firstname'].strip(),
            'lastname': groups['lastname'].strip(),
            'middlename': None
        }

    # Pattern 4: firstname lastname
    pattern4 = r'^(?P<firstname>[A-Za-z\sñÑ\u010D\u010D-]+)\s(?P<lastname>[A-Za-z\sñÑ\u010D\u010D-]+)$'
    match4 = re.match(pattern4, name)
    if match4:
        groups = match4.groupdict()
        return {
            'firstname': groups['firstname'].strip(),
            'lastname': groups['lastname'].strip(),
            'middlename': None
        }

    return None

    
# Custom JSON encoder class
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)
    

