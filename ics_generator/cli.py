import click
from .generator import generate_event_details, create_ics_file

@click.command()
@click.argument('prompt')
@click.option('--output', '-o', default='event.ics', help='Output ICS file path')
def main(prompt, output):
    """Generate an ICS calendar file from a natural language prompt."""
    try:
        # Generate event details using Claude
        click.echo("Generating event details...")
        event_details = generate_event_details(prompt)
        
        # Create ICS file
        output_file = create_ics_file(event_details, output)
        click.echo(f"Successfully created ICS file: {output_file}")
        
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main() 