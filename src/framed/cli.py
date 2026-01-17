import click
import sys
# from .config import load_config # implementation pending

@click.group()
def main():
    """Framed: Automated App Store Screenshot Tool"""
    pass

@main.command()
def init():
    """Initialize a new framed configuration"""
    click.echo("Initializing framed...")

@main.command()
def run():
    """Run the full screenshot generation pipeline"""
    from .config import load_config
    from .runner import Runner
    
    try:
        config = load_config()
        runner = Runner(config)
        runner.run()
        click.echo("✅ Pipeline completed!")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
