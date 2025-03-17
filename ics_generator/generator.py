import os
from datetime import datetime, timedelta
from openai import OpenAI
from icalendar import Calendar, Event, vRecur
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

def get_current_time():
    """Get current time in New York timezone."""
    ny_tz = pytz.timezone('America/New_York')
    return datetime.now(ny_tz)

def generate_event_details(prompt):
    """Use Claude to generate event details from a prompt."""
    client = OpenAI(
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        base_url="https://api.anthropic.com/v1/"
    )
    
    current_time = get_current_time()
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M")
    
    system_prompt = f"""You are an event planning assistant. The current time is {current_time_str} (New York time).
    Given a prompt, generate event details in EXACTLY the following format, with each field on a new line and exactly one colon between the field name and value:
    Title: [Event Title]
    Description: [Event Description]
    Start Time: [YYYY-MM-DD HH:MM] (if timezone is specified in prompt, append it as a space-separated value, e.g., "2024-03-17 14:00 America/Los_Angeles")
    Duration: [hours]
    Location: [Event Location]
    All Day: [true/false] (set to true for all-day events, false for timed events)
    Recurrence: [RRULE format if recurring, leave empty if not] (e.g., "FREQ=WEEKLY;BYDAY=MO,TH;UNTIL=20240430" for weekly on Mondays and Thursdays until April 30, 2024)
    
    When generating times, use the current time as reference. For example:
    - "tomorrow at 2 PM" should be the next day at 2 PM
    - "next Monday at 10 AM" should be the next Monday at 10 AM
    - "in 2 hours" should be current time + 2 hours
    - "all day meeting tomorrow" should set All Day to true
    - For recurring events, generate appropriate RRULE based on the description
    
    IMPORTANT: Each field must be on its own line with exactly one colon between the field name and value. Do not include any additional text or formatting."""
    
    response = client.chat.completions.create(
        model="claude-3-7-sonnet-20250219",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    
    # Parse the response
    response_text = response.choices[0].message.content
    event_details = {}
    
    # Debug output
    print("\nParsing response:")
    print(response_text)
    
    for line in response_text.split('\n'):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
            
        if ':' not in line:  # Skip lines without colon
            continue
            
        try:
            # Split on first colon only
            parts = line.split(':', 1)
            if len(parts) != 2:  # Skip if not exactly one colon
                continue
                
            key = parts[0].strip()
            value = parts[1].strip()
            
            if key and value:  # Only add if both key and value are non-empty
                event_details[key] = value
                print(f"Parsed: {key} = {value}")
        except Exception as e:
            print(f"Warning: Error parsing line '{line}': {str(e)}")
            continue
    
    # Validate required fields
    required_fields = ['Title', 'Description', 'Start Time', 'Duration']
    missing_fields = [field for field in required_fields if field not in event_details]
    if missing_fields:
        print("\nMissing required fields:", missing_fields)
        print("Available fields:", list(event_details.keys()))
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return event_details

def parse_duration(duration_str, default_hours=1):
    """Parse duration string and return hours as float."""
    try:
        # First try direct float conversion
        return float(duration_str)
    except ValueError:
        try:
            # Try parsing "X hours" format
            parts = duration_str.split()
            if parts:
                return float(parts[0])
        except (ValueError, IndexError):
            print(f"Warning: Could not parse duration '{duration_str}', using {default_hours} hour default")
            return default_hours

def parse_recurrence_rule(rrule_str):
    """Parse recurrence rule string into a vRecur object."""
    if not rrule_str:
        return None
        
    recur_dict = {}
    for part in rrule_str.split(';'):
        if '=' in part:
            k, v = part.split('=')
            if k == 'BYDAY':
                recur_dict[k] = v.split(',')
            else:
                recur_dict[k] = v
    
    return vRecur(recur_dict)

def create_ics_file(event_details, output_file='event.ics'):
    """Create an ICS file from event details."""
    cal = Calendar()
    
    # Create event
    event = Event()
    
    # Set event properties
    event.add('summary', event_details['Title'])
    event.add('description', event_details['Description'])
    
    # Check if this is an all-day event
    is_all_day = event_details.get('All Day', 'false').lower() == 'true'
    
    # Parse start time and handle timezone
    start_time_str = event_details['Start Time']
    try:
        # Clean up the string by removing any parentheses and their contents
        start_time_str = start_time_str.split('(')[0].strip()
        
        # Try to parse with timezone if provided
        parts = start_time_str.split()
        if len(parts) > 2:
            # If timezone is specified in the string
            timezone_str = parts[-1]
            timezone = pytz.timezone(timezone_str)
            start_time = datetime.strptime(' '.join(parts[:-1]), '%Y-%m-%d %H:%M')
            start_time = timezone.localize(start_time)
        else:
            # Use default New York timezone
            ny_tz = pytz.timezone('America/New_York')
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
            start_time = ny_tz.localize(start_time)
    except Exception as e:
        print(f"Warning: Could not parse timezone, using New York timezone. Error: {str(e)}")
        ny_tz = pytz.timezone('America/New_York')
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        start_time = ny_tz.localize(start_time)
    
    # Handle all-day events differently
    if is_all_day:
        # For all-day events, we only need the date part
        event.add('dtstart', start_time.date())
        # Add duration for all-day events (default to 1 day if not specified)
        duration_hours = parse_duration(event_details.get('Duration', '24'), default_hours=24)
        event.add('duration', timedelta(hours=duration_hours))
    else:
        # For regular events, use the full datetime
        event.add('dtstart', start_time)
        # Add duration
        duration_hours = parse_duration(event_details['Duration'])
        event.add('duration', timedelta(hours=duration_hours))
    
    # Add recurrence if specified
    if 'Recurrence' in event_details and event_details['Recurrence']:
        try:
            recur = parse_recurrence_rule(event_details['Recurrence'])
            if recur:
                event.add('rrule', recur)
        except Exception as e:
            print(f"Warning: Could not parse recurrence rule: {str(e)}")
    
    # Add location if provided
    if 'Location' in event_details and event_details['Location']:
        event.add('location', event_details['Location'])
    
    # Add event to calendar
    cal.add_component(event)
    
    # Write to file
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    return output_file

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: ics-generator \"<event description>\"")
        sys.exit(1)
    
    prompt = sys.argv[1]
    print(f"Generating event details...")
    
    try:
        event_details = generate_event_details(prompt)
        output_file = create_ics_file(event_details)
        print(f"Success! ICS file created: {output_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 