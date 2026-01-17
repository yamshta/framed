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

@main.command(name="template-help")
@click.option('--name', default='standard', help='Name of the template to inspect')
def template_help(name):
    """Show available settings for a template"""
    import yaml
    from pathlib import Path
    
    template_dir = Path(__file__).parent / "templates" / name
    config_path = template_dir / "template.yaml"
    
    if not config_path.exists():
        click.echo(f"❌ Template '{name}' not found or has no template.yaml")
        return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        click.echo(f"\n🎨 Template: {name}")
        click.echo(f"   {data.get('description', 'No description available')}")
        click.echo("\n🛠  Available Settings (for template_settings):")
        
        defaults = data.get('defaults', {})
        if not defaults:
            click.echo("   (No configurable settings)")
        else:
            for key, value in defaults.items():
                click.echo(f"   - {key}: (default: {value})")
        click.echo("")
        
    except Exception as e:
        click.echo(f"❌ Error reading template config: {e}", err=True)

if __name__ == "__main__":
    main()
