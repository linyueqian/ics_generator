import os
from datetime import datetime, timedelta
from openai import OpenAI
from icalendar import Calendar, Event
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
    Given a prompt, generate event details in the following format:
    Title: [Event Title]
    Description: [Event Description]
    Start Time: [YYYY-MM-DD HH:MM] (if timezone is specified in prompt, append it as a space-separated value, e.g., "2024-03-17 14:00 America/Los_Angeles")
    Duration: [hours]
    Location: [Event Location]
    All Day: [true/false] (set to true for all-day events, false for timed events)
    
    When generating times, use the current time as reference. For example:
    - "tomorrow at 2 PM" should be the next day at 2 PM
    - "next Monday at 10 AM" should be the next Monday at 10 AM
    - "in 2 hours" should be current time + 2 hours
    - "all day meeting tomorrow" should set All Day to true
    """
    
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
    
    for line in response_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            event_details[key.strip()] = value.strip()
    
    return event_details

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
        duration_str = event_details.get('Duration', '24')
        duration_hours = float(duration_str.split()[0])
        event.add('duration', timedelta(hours=duration_hours))
    else:
        # For regular events, use the full datetime
        event.add('dtstart', start_time)
        # Add duration
        duration_str = event_details['Duration']
        duration_hours = float(duration_str.split()[0])
        event.add('duration', timedelta(hours=duration_hours))
    
    # Add location if provided
    if 'Location' in event_details:
        event.add('location', event_details['Location'])
    
    # Add event to calendar
    cal.add_component(event)
    
    # Write to file
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    return output_file 