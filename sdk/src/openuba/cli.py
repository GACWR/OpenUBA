"""OpenUBA CLI — command-line interface for managing UBA models."""

import click

import openuba


@click.group()
@click.option("--api-url", envvar="OPENUBA_API_URL", default=None, help="OpenUBA API server URL")
@click.option("--token", envvar="OPENUBA_TOKEN", default=None, help="Authentication token")
@click.option("--model-dir", envvar="OPENUBA_MODEL_DIR", default=None, help="Local model storage directory")
def main(api_url, token, model_dir):
    """OpenUBA — User Behavior Analytics CLI"""
    if api_url or token or model_dir:
        openuba.configure(api_url=api_url, token=token, model_dir=model_dir)


@main.command()
@click.argument("model_name")
@click.option("--version", default=None, help="Model version to install")
@click.option("--source", default=None, help="Registry source (github, local, huggingface)")
def install(model_name, version, source):
    """Install a model from the openuba-model-hub registry.

    Downloads MODEL.py, model.yaml, and related files from
    https://github.com/GACWR/openuba-model-hub into ~/.openuba/models/.
    """
    click.echo(f"Installing {model_name}...")
    try:
        result = openuba.install(model_name, version=version, source=source)
        click.echo(
            f"Installed {result['name']} v{result.get('version', 'latest')} "
            f"({result['files_downloaded']} files)"
        )
        click.echo(f"Location: {result['path']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("model_name")
def uninstall(model_name):
    """Remove a locally installed model."""
    try:
        result = openuba.uninstall(model_name)
        click.echo(f"Uninstalled {result['name']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command("list")
@click.option("--source", default=None, help="Filter by runtime (sklearn, pytorch, etc.)")
@click.option("--installed", is_flag=True, help="Show only locally installed models")
def list_models(source, installed):
    """List available models from the openuba-model-hub registry."""
    try:
        if installed:
            models = openuba.list_installed()
            if not models:
                click.echo("No models installed. Run: openuba install <model_name>")
                return
            click.echo(f"{'Name':<25} {'Version':<10} {'Runtime':<15} {'Path'}")
            click.echo("-" * 80)
            for m in models:
                click.echo(
                    f"{m.get('name', '?'):<25} "
                    f"{m.get('version', '-'):<10} "
                    f"{m.get('runtime', '-'):<15} "
                    f"{m.get('path', '')}"
                )
        else:
            models = openuba.list_models(source=source)
            if not models:
                click.echo("No models found.")
                return
            click.echo(f"{'Name':<25} {'Version':<10} {'Runtime':<15} {'Description'}")
            click.echo("-" * 80)
            for m in models:
                desc = m.get("description", "")
                if len(desc) > 40:
                    desc = desc[:37] + "..."
                click.echo(
                    f"{m.get('name', '?'):<25} "
                    f"{m.get('version', '-'):<10} "
                    f"{m.get('runtime', '-'):<15} "
                    f"{desc}"
                )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("model_name")
@click.option("--data", default=None, help="Path to input data file (CSV, Parquet, JSON)")
@click.option("--param", "-p", multiple=True, help="Model parameter (key=value)")
def run(model_name, data, param):
    """Run an installed model locally.

    Loads MODEL.py from ~/.openuba/models/<model_name>/ and executes
    the model's infer() method with the provided data.
    """
    parameters = {}
    for p in param:
        if "=" not in p:
            click.echo(f"Error: parameter must be key=value, got: {p}", err=True)
            raise SystemExit(1)
        key, value = p.split("=", 1)
        parameters[key] = value

    click.echo(f"Running {model_name}...")
    try:
        result = openuba.run(model_name, data=data, parameters=parameters or None)
        click.echo(f"Status: {result.get('status', 'unknown')}")
        if "results" in result:
            records = result["results"]
            click.echo(f"Results: {len(records)} records")
            # Print first few results as a preview
            for r in records[:5]:
                click.echo(f"  {r}")
            if len(records) > 5:
                click.echo(f"  ... and {len(records) - 5} more")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("model_name")
def info(model_name):
    """Show details for a model from the registry."""
    try:
        model = openuba.get_model(model_name)
        click.echo(f"Name:        {model.get('name', '?')}")
        click.echo(f"Version:     {model.get('version', '-')}")
        click.echo(f"Runtime:     {model.get('runtime', '-')}")
        click.echo(f"Framework:   {model.get('framework', '-')}")
        click.echo(f"Author:      {model.get('author', '-')}")
        click.echo(f"License:     {model.get('license', '-')}")
        click.echo(f"Description: {model.get('description', '-')}")
        click.echo(f"Installed:   {'yes' if model.get('installed') else 'no'}")
        if model.get("installed"):
            click.echo(f"Path:        {model.get('install_path')}")
        tags = model.get("tags", [])
        if tags:
            click.echo(f"Tags:        {', '.join(tags)}")
        params = model.get("parameters", [])
        if params:
            click.echo(f"Parameters:")
            for p in params:
                click.echo(
                    f"  {p['name']:<20} {p.get('type', '?'):<10} "
                    f"default={p.get('default', '-')}  {p.get('description', '')}"
                )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
def version():
    """Show the OpenUBA SDK version."""
    click.echo(f"openuba {openuba.__version__}")


if __name__ == "__main__":
    main()
