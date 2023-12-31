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

from os import path

CURDIR = path.dirname(path.realpath(__file__))

TMPDIR = path.join(CURDIR, 'temp')
LAUNDIR = path.join(TMPDIR, '.minecraft')
INSTDIR = path.join(TMPDIR, 'gamedir')

ASSETDIR = path.join(CURDIR, 'assets')
MANIFEST = path.join(ASSETDIR, 'manifest.json')
LAUNPROF = path.join(ASSETDIR, 'launcher_profiles.json')
