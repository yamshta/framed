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
@click.option('--skip-capture', is_flag=True, help='Skip simulator capture and process existing raw screenshots only.')
def run(skip_capture):
    """Run the full screenshot generation pipeline"""
    from .config import load_config
    from .runner import Runner
    
    try:
        config = load_config()
        runner = Runner(config)
        runner.run(skip_capture=skip_capture)
        click.echo("✅ Pipeline completed!")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@main.command(name="list-templates")
def list_templates():
    """List all available templates"""
    from pathlib import Path
    import yaml
    
    templates_dir = Path(__file__).parent / "templates"
    if not templates_dir.exists():
        click.echo("❌ No templates found.")
        return
        
    click.echo("\n📋 Available Templates:\n")
    
    for item in templates_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            config_path = item / "template.yaml"
            desc = "No description available"
            
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        desc = data.get('description', desc)
                except:
                    pass
            
            click.echo(f"  ✨ {item.name}:")
            click.echo(f"      {desc}")

    click.echo("")

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

@main.command(name="generate-samples")
@click.option('--template', '-t', default=None, help='Generate samples for a specific template only')
def generate_samples(template):
    """Generate sample images for all (or specific) templates"""
    from pathlib import Path
    from .config import load_config, Config
    from .processor import Processor
    import shutil
    
    templates_dir = Path(__file__).parent / "templates"
    framed_root = Path(__file__).parent.parent.parent
    sample_raws = framed_root / "sample_raws" / "ja"
    
    if not sample_raws.exists():
        click.echo(f"❌ sample_raws/ja not found at {sample_raws}")
        click.echo("   Please add raw screenshots to sample_raws/ja/")
        return
    
    click.echo("\n🎨 Generating samples...\n")
    
    generated = 0
    templates_to_process = []
    
    for item in sorted(templates_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('__'):
            if template and item.name != template:
                continue
            templates_to_process.append(item)
    
    if template and not templates_to_process:
        click.echo(f"❌ Template '{template}' not found")
        return
    
    for item in templates_to_process:
        samples_dir = item / "samples"
        framed_yaml = samples_dir / "framed.yaml"
        
        if not framed_yaml.exists():
            click.echo(f"  ⏭️  {item.name}: No samples/framed.yaml, skipping")
            continue
        
        click.echo(f"  📸 {item.name}...")
        
        try:
            # Clean up old sample images first
            for old_png in samples_dir.glob("*.png"):
                old_png.unlink()
            
            # Create temporary raw directory structure for processing
            temp_raw_dir = samples_dir / "raw" / "raws_ja"
            temp_raw_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy raw files
            for png in sample_raws.glob("*.png"):
                shutil.copy2(png, temp_raw_dir / png.name)
            
            # Load config and process
            import os
            original_cwd = os.getcwd()
            os.chdir(samples_dir)
            
            try:
                config = load_config("framed.yaml")
                processor = Processor(config)
                processor.process()
                
                # Copy output to samples root
                output_dir = samples_dir / "framed" / "raws_ja"
                if output_dir.exists():
                    for png in output_dir.glob("*.png"):
                        dest = samples_dir / png.name
                        shutil.copy2(png, dest)
                        generated += 1
                
                click.echo(f"     ✅ Done")
            finally:
                os.chdir(original_cwd)
                # Cleanup temp directories
                shutil.rmtree(samples_dir / "raw", ignore_errors=True)
                shutil.rmtree(samples_dir / "framed", ignore_errors=True)
                
        except Exception as e:
            click.echo(f"     ❌ Error: {e}")
    
    click.echo(f"\n✅ Generated {generated} sample images")

if __name__ == "__main__":
    main()
