import json
import re
from django import template

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

class GradeInfo:
    """Simple object to hold grade information for template access"""
    def __init__(self, grade, band, emoji, color):
        self.grade = grade
        self.band = band
        self.emoji = emoji
        self.color = color

@register.filter
def letter_grade(risk_score):
    """
    Converts numeric risk score (0-100) to letter grade with band and emoji.
    Returns GradeInfo object with: grade, band, emoji, color
    
    Bands:
    - A+/A/A- → Safe
    - B+/B/B-/C+/C/C- → Caution
    - D+/D/D-/F → High Risk
    """
    if risk_score is None:
        return GradeInfo('N/A', 'Unknown', '⚪', 'gray')
    
    try:
        score = float(risk_score)
    except (ValueError, TypeError):
        return GradeInfo('N/A', 'Unknown', '⚪', 'gray')
    
    # Determine letter grade
    if score <= 2:
        return GradeInfo('A+', 'Safe', '🟢', 'green')
    elif score <= 7:
        return GradeInfo('A', 'Safe', '🟢', 'green')
    elif score <= 9:
        return GradeInfo('A-', 'Safe', '🟢', 'green')
    elif score <= 12:
        return GradeInfo('B+', 'Caution', '🟠', 'amber')
    elif score <= 17:
        return GradeInfo('B', 'Caution', '🟠', 'amber')
    elif score <= 19:
        return GradeInfo('B-', 'Caution', '🟠', 'amber')
    elif score <= 22:
        return GradeInfo('C+', 'Caution', '🟠', 'amber')
    elif score <= 27:
        return GradeInfo('C', 'Caution', '🟠', 'amber')
    elif score <= 29:
        return GradeInfo('C-', 'Caution', '🟠', 'amber')
    elif score <= 32:
        return GradeInfo('D+', 'High Risk', '🔴', 'red')
    elif score <= 37:
        return GradeInfo('D', 'High Risk', '🔴', 'red')
    elif score <= 39:
        return GradeInfo('D-', 'High Risk', '🔴', 'red')
    else:
        return GradeInfo('F', 'High Risk', '🔴', 'red')

@register.filter
def letter_grade(risk_score):
    """
    Convert a numeric risk score (0-100) to a letter grade (A+ to F).
    Matches the grading scale used across all platforms.
    """
    if risk_score is None:
        return 'N/A'
    
    try:
        score = int(risk_score)
    except (ValueError, TypeError):
        return 'N/A'
    
    if score <= 2:
        return 'A+'
    elif score <= 7:
        return 'A'
    elif score <= 9:
        return 'A-'
    elif score <= 12:
        return 'B+'
    elif score <= 17:
        return 'B'
    elif score <= 19:
        return 'B-'
    elif score <= 22:
        return 'C+'
    elif score <= 27:
        return 'C'
    elif score <= 29:
        return 'C-'
    elif score <= 32:
        return 'D+'
    elif score <= 37:
        return 'D'
    elif score <= 39:
        return 'D-'
    else:
        return 'F'
