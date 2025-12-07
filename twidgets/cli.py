import argparse
import sys
import shutil
import pathlib
import typing
from . import main as app_main
from . import __version__

# Use the modern 'files()' API (has a fallback for Python 3.8, but not used.)
# except ImportError:
# Fallback for Python < 3.9 not needed, this only runs with Python 3.10+
# from importlib_resources import files, as_file
from importlib.resources import files, as_file


def init_command(args: typing.Any) -> None:
    """Handles the 'twidgets init' subcommand."""

    try:
        # 'twidgets.config' maps to the 'twidgets/config/' directory
        source_config_dir_traversable = files('twidgets.config')
    except ModuleNotFoundError:
        print('Error: Could not find the package config files. Is \'twidgets\' installed correctly?', file=sys.stderr)
        sys.exit(1)

    dest_config_dir = pathlib.Path.home() / '.config' / 'twidgets'

    # Create destination directory
    try:
        dest_config_dir.mkdir(parents=True, exist_ok=True)
        print(f'Created config directory: {dest_config_dir}')
    except OSError as e:
        print(f'Error: Could not create directory {dest_config_dir}. {e}', file=sys.stderr)
        sys.exit(1)

    # --- Improved File Copying Logic ---
    with as_file(source_config_dir_traversable) as source_config_path:

        print(f'Copying config files to {dest_config_dir}...')

        # Define allowed extensions
        allowed_extensions = {'.yaml', '.yml', '.env', '.env.example', '.example', '.txt'}

        # Iterate ONCE to find all relevant files
        files_to_copy = [
            f for f in source_config_path.rglob('*')
            if f.suffix in allowed_extensions and f.is_file()
        ]

        if not files_to_copy:
            print('Warning: No config files (.yaml, .yml, .env, .env.example, .example, .txt) found in the package.',
                  file=sys.stderr)
            return

        for source_file in files_to_copy:
            # Recreate the relative path in the destination
            relative_path = source_file.relative_to(source_config_path)

            # rename .env.example -> .env
            if source_file.name.endswith('.env.example'):
                # Replace only the filename, keep the directory
                relative_path = relative_path.with_name(
                    relative_path.name[:-len('.example')]
                )

            dest_file = dest_config_dir / relative_path

            # Ensure the file's parent directory exists in the destination
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # Check for --force flag
            if not dest_file.exists() or args.force:
                try:
                    shutil.copy2(source_file, dest_file)
                    print(f'  Copied: {relative_path}')
                except OSError as e:
                    print(f'  Error copying {relative_path}: {e}', file=sys.stderr)
            else:
                print(f'  Skipped (exists): {relative_path}')

    print('\nInitialization complete.')
    print(f'Your configuration files are in: {dest_config_dir}')


def main() -> None:
    """Main entry point for the 'twidgets' command."""

    # Adding prog='twidgets' improves the help message
    parser = argparse.ArgumentParser(
        description='Terminal Widgets main command',
        prog='twidgets'
    )

    # Add global --version flag
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
        help='Show the program version'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'init' subcommand
    init_parser = subparsers.add_parser('init', help='Initialize user configuration files')
    init_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite existing configuration files'
    )
    init_parser.set_defaults(func=init_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        # A subcommand was called (e.g., 'init')
        args.func(args)
    else:
        # No subcommand given, run the main application
        try:
            app_main.main_entry_point()
        except KeyboardInterrupt:
            print('\nExiting.')
            sys.exit(0)


if __name__ == '__main__':
    main()
