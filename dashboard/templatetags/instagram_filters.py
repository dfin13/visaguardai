import json
import re
from django import template
from dashboard.grading_system import risk_score_to_letter_grade, format_grade_display

register = template.Library()

@register.filter
def parse_json(value, path):
    try:
        data = json.loads(value.strip('```json\n').strip('```'))
        keys = path.split('.')
        for key in keys:
            data = data.get(key, {})
        return data if data else "No data"
    except (json.JSONDecodeError, AttributeError):
        return "Error parsing analysis"

@register.filter
def extract_hashtags(text):
    return re.findall(r'#(\w+)', text)




# filters.py
import json
from django import template

register = template.Library()

@register.filter
def parse_instagram_analysis(value):
    """
    Filter to parse Instagram analysis JSON string into Python objects
    """
    try:
        # Remove the ```json and ``` markers if present
        if value.startswith('```json'):
            value = value.replace('```json', '').replace('```', '').strip()
        
        # Parse the JSON
        data = json.loads(value)
        return data
    except (json.JSONDecodeError, AttributeError):
        return {}
@register.filter
def get_item(data, key):
    print(f"Type: {type(data)}, Key: '{key}', Value: {data}")
    
    # If it's a list of dictionaries with the key you're looking for
    if isinstance(data, list):
        if key.isdigit():  # Access by index
            try:
                return data[int(key)]
            except (ValueError, IndexError):
                return ''
        else:  # Look for the key in each dictionary
            for item in data:
                if isinstance(item, dict) and key in item:
                    return item[key]
            return ''
    
    # If it's a dictionary
    elif isinstance(data, dict):
        return data.get(key, '')
    
    return ''


import json
import re
@register.filter(name='clean_json')
def clean_json(value):
    """
    Cleans analysis strings like ```json ... ``` into plain JSON.
    """
    if not value:
        return []

    if value.startswith("```json") or value.startswith("``` json"):
        clean_data = value.strip("`")  # remove backticks
        clean_data = clean_data.replace("json", "", 1).strip()  # remove 'json'
    else:
        clean_data = value.strip()

    return clean_data

@register.filter
def remove_json_comments(value):
    """
    Removes JS-style '//' comments from JSON-like strings.
    Example:
    input:  '{ "a": 1 }, // comment \n { "b": 2 }'
    output: '{ "a": 1 },  \n { "b": 2 }'
    """
    if not isinstance(value, str):
        return value
    return re.sub(r'//.*', '', value)

@register.filter(name='to_letter_grade')
def to_letter_grade(score):
    """Convert risk score to letter grade info."""
    if score is None or score < 0:
        return {
            'grade': 'N/A',
            'descriptor': 'Unknown',
            'color': 'gray',
            'emoji': '⚪',
            'tailwind_color': 'text-gray-500',
            'bg_color': 'bg-gray-900/20',
            'border_color': 'border-gray-500/30',
            'numeric_score': -1
        }
    return risk_score_to_letter_grade(score)

@register.filter(name='format_grade')
def format_grade(score):
    """Format grade display."""
    if score is None or score < 0:
        return "N/A (Unknown) ⚪"
    return format_grade_display(score)
