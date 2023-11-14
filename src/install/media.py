# MCM-Manager: Minecraft Modpack Manager
# Copyright (C) 2023  Tygo Everts
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from json import load
from os import path, mkdir
from urllib import parse, request, error

from .headers import headers
from .urls import media_url
from .loadingbar import loadingbar

from ._types import Media, Manifest, MediaList, Side


class prepare:
    def __new__(cls, install_path: str, side: Side, manifest: Manifest) -> int:
        "Get the file size and check media validity while listing all media"

        # Define the class variables
        cls.install_path = install_path
        cls.side: Side = side

        # Prepare the media
        total_size = 0

        for media_type, media_list in {
            'mod': manifest.get('mods', []),
            'resourcepack': manifest.get('resourcepacks', []),
            'shaderpack': manifest.get('shaderpacks', [])
        }.items():
            total_size += cls.prepare_media(media_type, media_list)

        # At the end, return the total mods size
        return total_size

    @classmethod
    def load_manifest(cls, filename: str) -> Manifest:
        "Load a manifest file and validate it's general contents"
        with open(filename) as json_file:
            manifest = load(json_file)

        # Check for validity
        if manifest.get('minecraft') is None:
            raise KeyError("The modpack must include a 'minecraft' section.")
        if manifest['minecraft'].get('version') is None:
            raise KeyError(
                "The 'minecraft' section must include the minecraft version.")
        if manifest['minecraft'].get('modloader') is None or \
                '-' not in manifest['minecraft']['modloader']:
            raise KeyError(
                "The 'minecraft' section must include the modloader " +
                "and version in this format: 'modloader-x.x.x'")

        return manifest

    @classmethod
    def check_media_validity(cls, media_list: MediaList, media_type: str) -> None:
        "Check for the modpack file validity"
        for media in media_list:
            for key in ['type', 'slug', 'name']:
                if key not in media:
                    raise KeyError(
                        f"The '{key}' key should be specified " +
                        f"in the following {media_type}: {media}."
                    )
            if media['type'] not in ['cf', 'mr', 'pm', 'url']:
                raise KeyError(
                    f"The type '{media['type']}' does not exist: {media}."
                )

            # Add a media['sides'] to all media, default ['client', 'server']
            sides: list[Side] = ['client', 'server']
            if 'sides' not in media.keys():
                media['sides'] = sides

    @classmethod
    def get_headers(cls, media: Media, url: str) -> int:
        "Recieve the content-length headers"
        try:
            size = int(request.urlopen(
                url).headers.get('content-length', 0))
        except error.HTTPError:
            try:
                # When returning an HTTP error, try again
                # while mimicking a common browser user agent
                size = int(request.urlopen(request.Request(
                    url, headers=headers)).headers.get('content-length', 0))
            except error.HTTPError as e:
                print(f"! WARNING: Could not download {media['name']}: \n{e}")

                return 0
        except error.URLError as e:
            if e.reason.__str__() in ("[Errno -2] Name or service not known", "[Errno 11001] getaddrinfo failed"):
                print(f"! WARNING: The mod {media['name']}" +
                      f"was not found: {e.reason}")
                return 0
            else:
                raise e

        # Add the size to the tuple
        if '_dl' in media:
            media['_dl'] = media['_dl'][:-1] + (size,)

        return size

    @classmethod
    def prepare_media(cls, media_type: str, media_list: MediaList) -> int:
        if len(media_list) == 0:
            return 0

        cls.check_media_validity(media_list, media_type)

        # List the installed media and prepare the modpack
        print(f"\n{media_type.capitalize()}s: ")

        size = 0
        for media in (media for media in media_list if cls.side in media['sides']):
            # Add the corresponding download info to media['_dl']
            url = media_url(media)

            dl_path = path.join(
                cls.install_path,
                media_type + 's',
                parse.unquote(media['name'])
            )

            media['_dl'] = (
                url, dl_path, 0
            )

            # Append the media size to the total size and save it in media['_dl']
            size += cls.get_headers(media, url)

            # Print the media name
            print(f"  {media['slug']} ({parse.unquote(media['name'])})")

        # At the end, return the total media size
        return size


def download_files(total_size: int, install_path: str, side: Side, manifest: Manifest) -> None:
    "Download all files using a tqdm loading bar"

    mods: MediaList = manifest.get('mods', [])
    resourcepacks: MediaList = manifest.get('resourcepacks', [])
    shaderpacks: MediaList = manifest.get('shaderpacks', [])

    for folder, media_list in {
        'mods': mods,
        'resourcepacks': resourcepacks,
        'shaderpacks': shaderpacks
    }.items():
        if len(media_list) != 0 and not path.isdir(path.join(install_path, folder)):
            mkdir(path.join(install_path, folder))

    print('\033[?25l')  # Hide the cursor
    skipped_files = 0

    # Genereate the iterator
    iterator: list[tuple[str, str, int, list[Side]]] = []

    for media in mods + resourcepacks + shaderpacks:
        if "_dl" not in media:
            continue
        item: tuple[str, str, int, list[Side]] = (
            *media['_dl'], media['sides'])
        iterator.append(item)

    # Download everything with a loading bar
    with loadingbar(
        total=total_size,
        unit='B',
        show_desc=True,
        disappear=True
    ) as bar:
        bar: loadingbar[int]  # The only way it worked out
        for url, fname, size, sides in iterator:
            if side not in sides:
                # As the size isn't calculated, it
                # doesn't have to update the bar
                continue

            if path.isfile(fname):
                skipped_files += 1

                # Inform it's already installed
                bar.update(size)
                bar.set_desc(parse.unquote(path.basename(fname)) +
                             " is already installed, skipping...")

                continue

            # Set the description
            file = parse.unquote(path.basename(fname))
            bar.set_desc(f"Downloading {file}...")

            try:
                # Download the file
                with request.urlopen(url) as resp:
                    # Write the file
                    with open(fname, 'wb') as media_file:
                        while True:
                            # Read the response data
                            data = resp.read(1024)

                            # Break if it's complete
                            if not data:
                                break

                            # Update the bar
                            part_size = media_file.write(data)
                            bar.update(part_size)
            except error.HTTPError:
                # If the file is denied, it tries again while
                # mimicking a common browser user agent
                try:
                    with request.urlopen(request.Request(url, headers=headers)) as resp:
                        with open(fname, 'wb') as media_file:
                            while True:
                                data = resp.read(1024)
                                if not data:
                                    break
                                part_size = media_file.write(data)
                                bar.update(part_size)
                except error.HTTPError:
                    pass  # The user has already been warned
            except error.URLError:
                pass  # The user has already been warned

    print('\033[?25h')  # Show the cursor

    total_files = len([media for media in mods +
                      resourcepacks + shaderpacks if side in media.get('sides', [])])

    print(f"Skipped {skipped_files}/{total_files} " +
          "files that were already installed" if skipped_files != 0 else '',
          sep=''
          )
