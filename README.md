# ICS Generator

A command-line tool that generates ICS calendar files using natural language prompts. It uses Claude AI to understand your event descriptions and creates properly formatted calendar events.

## Features

- Generate calendar events using natural language
- Support for all-day events
- Automatic timezone handling (defaults to New York timezone)
- Support for multiple timezones
- Generates standard ICS files compatible with most calendar applications

## Installation

1. Clone the repository:
```bash
git clone https://github.com/linyueqian/ics_generator.git
```

2. Install the package:
```bash
pip install -e .
```

3. Create a `.env` file in your home directory with your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

After installation, you can use the `ics-generator` command from anywhere:

```bash
# Basic usage
ics-generator "Schedule a meeting tomorrow at 2 PM"

# Specify output file
ics-generator "Create an all-day conference next Monday" -o conference.ics

# With timezone
ics-generator "Schedule a call for 10 AM Pacific time tomorrow"
```

### Examples

```bash
# Regular meeting
ics-generator "Schedule a team meeting tomorrow at 2 PM"

# All-day event
ics-generator "Create an all-day workshop on Friday"

# Event with specific timezone
ics-generator "Plan a call with the London team at 3 PM London time tomorrow"

# Event with custom output file
ics-generator "Schedule a doctor's appointment next Monday at 10 AM" -o appointment.ics
```

## Requirements

- Python 3.6 or higher
- Anthropic API key
- Required Python packages (installed automatically):
  - openai
  - icalendar
  - python-dotenv
  - pytz
  - click

## License

MIT License 