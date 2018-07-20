## Config parsing utility file
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright David Chan, 2018

def parse(config_file_location):
    CFG = {}
    with open(config_file_location,'r') as cfg_file:
        for line in cfg_file:
            if len(line.strip()) == 0:
                continue
            elif line.strip()[0] == '#':
                continue
            else:
                tok = line.split('=')
                key = tok[0].strip()
                value = tok[1].strip() if tok[1][-1] != '\n' else tok[1][:-1].strip()
                if key in CFG:
                    # If it's already a list, we'll just append, otherwise
                    # we need to make it into a list
                    if type(CFG[key]) == list:
                        CFG[key].append(value)
                    else:
                        CFG[key] = [CFG[key], value]
                else:
                    CFG[key] = value
    return CFG