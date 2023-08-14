from json import load
from os import path, get_terminal_size, mkdir
from tqdm import tqdm
from typing import Any
from install import filesize, mods


def download_files(total_size: int, install_path: str, mod_list: list[dict[str, Any]]):
    """Download all files with a tqdm loading bar"""
    if not path.isdir(path.join(install_path, 'mods')):
        mkdir(path.join(install_path, 'mods'))

    print('\033[?25l')  # Hide the cursor
    skipped_mods = 0

    with tqdm(
        total=total_size,
        position=1,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        bar_format='{desc}'
    ) as outer_bar:
        for url, fname, size in (inner_bar := tqdm(
            [mod['_'] for mod in mod_list],
            position=0,
            unit='B',
            unit_scale=True,
            total=total_size,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                leave=False)):
            skipped_mods = mods.download_mods(  # type: ignore
                url, fname, size, skipped_mods, outer_bar, inner_bar)

    print('\033[2A\033[?25h')  # Go two lines back and show cursor

    # Make a new bar that directly updates to 100% as
    # the last one will dissapear after the loop is done
    if total_size != 0:
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}'
        ) as bar:
            bar.update(total_size)
    else:
        with tqdm(
            total=1,
            unit='it',
            bar_format='{percentage:3.0f}%|{bar}| 0.00/0.00'
        ) as bar:
            bar.update(1)

    print(' ' * (get_terminal_size().columns) + '\r', end='')
    print(
        f"Skipped {skipped_mods}/{len(mod_list)} mods that were already installed" if skipped_mods != 0 else '')


def install(manifest_file: str, install_path: str = path.dirname(path.realpath(__file__)), confirm: bool = True) -> None:
    """
    Install a list of mods, resourcepacks, shaderpacks and config files. Arguments:

    :param manifest_file: This should be a path to a
    manifest file. The file structure:

    ```json
    {
        "minecraft": {
            "version": "(version)",
            "modloader": "(modloader)-(modloader version)"
        },
        "mods": [
            {
                "type": "(type)",
                "slug": "(slug)",
                "name": "(filename)"
            }
        ]
    }
    ```

    :param install_path: The base path everything should be installed to
    :param confirm: If the user should confirm the download
    """

    # Import the manifest file
    with open(manifest_file) as json_file:
        manifest: dict[str, Any] = load(json_file)

    # Check for validity
    if manifest.get('minecraft', None) is None:
        raise KeyError("The modpack must include a 'minecraft' section.")
    if manifest['minecraft'].get('version', None) is None:
        raise KeyError(
            "The 'minecraft' section must include the minecraft version.")
    if manifest['minecraft'].get('modloader', None) is None or \
            '-' not in manifest['minecraft']['modloader']:
        raise KeyError(
            "The 'minecraft' section must include the modloader " +
            "and version in this format: 'modloader-x.x.x'")

    # List the modpack info
    modpack_version: str = manifest['minecraft']['version']
    modloader: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[0]
    modloader_version: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[1]

    print(f"Modpack version: {modpack_version}\n" +
          f"Mod loader: {modloader}\n"
          f"Mod loader version: {modloader_version}")

    total_size = 0

    if manifest.get('mods', None) is not None:
        total_size = mods.prepare_mods(
            total_size, install_path, manifest['mods'])

    print(
        f"\n{len(manifest.get('mods', []))} mods, 0 recourcepacks, 0 shaderpacks\n" +
        f"Total file size: {filesize.size(total_size, system=filesize.alternative)}")  # type: ignore

    # Ask for confirmation if confirm is True and install all modpacks
    if confirm == True:
        if input("Continue? (Y/n) ").lower() not in ['y', '']:
            print("Cancelling...\n")
            exit()
    else:
        print("Continue (Y/n) ")

    # Download all files
    download_files(total_size, install_path, manifest.get('mods', []))


install(path.join(path.dirname(path.realpath(__file__)), 'example-manifest.json'))
