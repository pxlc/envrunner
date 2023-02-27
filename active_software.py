# -----------------------------------------------------------------------------
# MIT License
#
# Copyright (c) 2023 pxlc
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

import os
import re
import json

from .os_util import os_info, conform_path_slash


DEV_TAG_REGEX = re.compile(r'[a-zA-Z][a-zA-Z0-9_]+')


class ActiveSoftwareSnapshot(object):

    DEPEND_SW_VER_PATTERN = r'\[@[a-zA-Z0-9_\-]+:(?:.*\{[A-Z]+\}.*)+\]'
    VER_TOKEN_PATTERN = r'\{([A-Z]+)\}'

    DEPEND_SW_VER_REGEX = re.compile(DEPEND_SW_VER_PATTERN)
    VER_TOKEN_REGEX = re.compile(VER_TOKEN_PATTERN)

    def __init__(self, active_sw_list, sw_defs_d, prj_code, prj_sw_versions_d,
                 path_slash=None):

        self.active_sw_list = active_sw_list
        self.active_sw_name_list = [sw_name.split('@')[0] for sw_name in
                                                            active_sw_list]

        self.info_by_active_sw = {}
        self.sw_versions_d = prj_sw_versions_d
        self.prj_code = prj_code
        self.path_slash = path_slash if path_slash is not None else os.sep

        self.sw_info_is_generated = False

        self.active_sw_defs_d = self._build_active_sw_info(sw_defs_d)

    def get_active_sw_names(self):

        return self.active_sw_name_list

    def get_sw_install_path(self, sw_name):

        return self.info_by_active_sw[sw_name]['install_location']

    def get_sw_info(self, sw_name):

        return self.info_by_active_sw[sw_name]

    def get_sw_version(self, sw_name):

        sw_info = self.info_by_active_sw[sw_name]
        if 'version_info' in sw_info:
            return sw_info['version_info']['VER']
        elif sw_info['override_version']:
            return sw_info['override_version']
        else:
            raise Exception(
                'No version or dev tag specified for sw "%s"' % sw_name)

    def get_sw_version_info(self, sw_name):

        sw_info = self.info_by_active_sw[sw_name]
        if 'version_info' in sw_info:
            return sw_info['version_info']
        elif sw_info['override_version']:
            return {'VER': sw_info['override_version']}
        else:
            raise Exception(
                'No version or dev tag specified for sw "%s"' % sw_name)

    def is_sw_dev_installed(self, sw_name):

        return self.info_by_active_sw[sw_name]['is_dev_install']

    def _build_version_format_regex(self, version_format_str):

        replace_d = {
            '.': '\\.',
            '{MAJOR}': '(?P<MAJOR>\d+)',
            '{MINOR}': '(?P<MINOR>\d+)',
            '{BUILD}': '(?P<BUILD>\d+)',
            '{REVISION}': '(?P<REVISION>\d+)',
        }

        version_regex_pattern = '^%s$' % version_format_str

        for replace_key in replace_d.keys():
            version_regex_pattern = version_regex_pattern.replace(
                                        replace_key, replace_d[replace_key])

        return (version_regex_pattern, re.compile(version_regex_pattern))

    def _expand_embedded_dependant_sw_versions(self, input_str):

        all_embedded_str_list = self.DEPEND_SW_VER_REGEX.findall(input_str)
        if not all_embedded_str_list:
            return {}
        embed_dep_d = {}
        for embedded_str in all_embedded_str_list:
            ver_tokens = self.VER_TOKEN_REGEX.findall(embedded_str)
            str_to_expand = embedded_str.split(':')[1][:-1]
            sw_name = embedded_str.split(':')[0].split('@')[1]
            embed_dep_d[embedded_str] = {
                'sw_dep_name': sw_name,
                'ver_tokens': ver_tokens,
                'str_to_expand': str_to_expand,
            }
        return embed_dep_d

    def _get_specific_install_location(self, install_loc_d):

        raw_install_loc_str = None

        for os_specificity in os_info.specificity_list:
            if os_specificity in install_loc_d:
                value = install_loc_d[os_specificity]
                if type(value) is list:
                    for raw_path in value:
                        if os.path.exists(os.path.expandvars(raw_path)):
                            raw_install_loc_str = raw_path
                            break
                    if not raw_install_loc_str:
                        raw_install_loc_str = value[-1] # assume last is default
                else:
                    # otherwise assume it is a string value for location
                    raw_install_loc_str = value
                break
        if not raw_install_loc_str and '_all' in install_loc_d:
            value = install_loc_d['_all']
            if type(value) is list:
                for raw_path in value:
                    if os.path.exists(os.path.expandvars(raw_path)):
                        raw_install_loc_str = raw_path
                        break
                if not raw_install_loc_str:
                    raw_install_loc_str = value[-1] # assume last is default
            else:
                # otherwise assume it is a string value for location
                raw_install_loc_str = value

        return raw_install_loc_str

    def _build_active_sw_info(self, sw_defs_d):

        self.info_by_active_sw = {}

        for active_sw in self.active_sw_list:
            override_version = None
            override_install_loc = None
            is_dev_install = False

            if '@' in active_sw:
                active_sw, directive = active_sw.split('@')
                bits = directive.split('|')
                if bits[0] == 'v':
                    # this is an override version number
                    override_version = bits[1]
                elif bits[0] == 'dev':
                    is_dev_install = True
                    # this is an override dev install path
                    if len(bits) != 3:
                        raise Exception(
                            'Override dev install path directive does not '
                            'have the correct number of parts (needs 3), '
                            'expecting: "dev", "<dev_tag>", "<path_spec>"')
                    if not DEV_TAG_REGEX.match(bits[1]):
                        raise Exception(
                            'Override dev install path directive specifies '
                            'a dev tag that does not conform to naming '
                            'convention (must begin with alpha, upper or '
                            'lower case and then one or more alphanumeric or '
                            'underscore characters)'
                        )
                    override_version = bits[1]
                    path_by_os_spec = {
                        os_spec: path for (os_spec, path) in
                        [entry.split('=') for entry in bits[2].split(',')]
                    }
                    for os_spec in os_info.specificity_list:
                        if os_spec in path_by_os_spec:
                            override_install_loc = path_by_os_spec[os_spec]
                            break
                    if not override_install_loc:
                        raise Exception(
                            'Override dev install path directive did not '
                            'specify a path for the current OS (%s)' %
                            os_info.os)

            if active_sw not in sw_defs_d and not override_install_loc:
                raise Exception(
                        'No definition found for software "%s"' % active_sw)

            sw_def = sw_defs_d[active_sw] if not is_dev_install else None

            ver_pattern = None
            ver_regex = None

            raw_install_loc_str = None
            if override_install_loc:
                raw_install_loc_str = override_install_loc
            else:
                install_loc_d = sw_def['install_location']
                raw_install_loc_str = self._get_specific_install_location(
                                                            install_loc_d)

            if not raw_install_loc_str:
                raise Exception(
                    'Install location for os "%s" is not defined'
                    ' for software "%s"' % (os_info.os, active_sw))

            if not is_dev_install:
                ver_pattern, ver_regex = self._build_version_format_regex(
                                                    sw_def['version_format'])

            self.info_by_active_sw[active_sw] = {
                'install_location':
                        # TODO: add processing of root paths here when root
                        #       paths module is ready.
                        os.path.expandvars(
                            os.path.expanduser(raw_install_loc_str)),
                'version_format': (sw_def['version_format']
                                        if not is_dev_install else None),
                'version_pattern': ver_pattern, # will be None if is_dev True
                'version_regex': ver_regex, # will be None if is_dev True
                'override_version': override_version,
                'override_install_loc': override_install_loc,
                'is_dev_install': is_dev_install,
            }

            if is_dev_install:
                self.info_by_active_sw[active_sw]['version_info'] = {
                                                    'VER': override_version}

        # end of "for active_sw ..."

        # Now loop through info_by_active_sw dict to capture version numbers
        # based on project config or based on override version, skipping
        # any direct dev installs
        #
        sw_need_version_list = [
            sw for sw in self.info_by_active_sw.keys()
                if not self.info_by_active_sw[sw]['is_dev_install']]

        for active_sw in sw_need_version_list:

            sw_info = self.info_by_active_sw[active_sw]
            if (active_sw not in self.sw_versions_d and
                    sw_info['override_version'] is None):
                raise Exception(
                    'Version for sw "%s" is not specified in project sw '
                    'versions and not provide as an override version or as '
                    'a direct path dev version' % active_sw)
            # at this point we either have an override version or a version
            # specified by the project config
            version = None
            if sw_info['override_version']:
                version = sw_info['override_version']
            else:
                version = self.sw_versions_d[active_sw]

            regex_result = sw_info['version_regex'].match(version)
            if not regex_result:
                raise Exception(
                    'Version "%s" provided for sw "%s" is not valid - the '
                    'regex pattern for its formatting is "%s"' % (
                            version, active_sw, sw_info['version_pattern']))

            version_info = {'VER': version}
            version_info.update(regex_result.groupdict())

            sw_info['version_info'] = version_info

        # Loop through and expand install loction paths with version info and
        # dependant sw version info
        for active_sw in sw_need_version_list:
            sw_info = self.info_by_active_sw[active_sw]
            install_loc = sw_info['install_location']

            # first expand dependant software version tags, e.g.
            # [@maya:{MAJOR}] or [@python:{MAJOR}{MINOR}] if there are any
            if '[@' in install_loc:
                embed_dep_d = self._expand_embedded_dependant_sw_versions(
                                                                install_loc)
                for embedded_str in embed_dep_d.keys():
                    info_d = embed_dep_d[embedded_str]
                    str_to_expand = info_d['str_to_expand']
                    sw_dep_name = info_d['sw_dep_name']
                    if sw_dep_name not in sw_need_version_list:
                        raise Exception(
                            'Dependency sw "%s" is not in list of active sw '
                            'to determine a version number for, so no '
                            'version information is available for it. Unable '
                            'to expand this embedded sw dependency version '
                            'for sw "%s"' % (sw_dep_name, active_sw))

                    sw_dep_info = self.info_by_active_sw[sw_dep_name]
                    sw_dep_ver_info = sw_dep_info['version_info']
                    replacement_str = str_to_expand.format(**sw_dep_ver_info)
                    install_loc = install_loc.replace(embedded_str,
                                                      replacement_str)

            install_loc = os.path.expandvars(install_loc)
            install_loc = install_loc.format(**sw_info['version_info'])
            sw_info['install_location'] = conform_path_slash(install_loc,
                                                             self.path_slash)
        
        self.sw_info_is_generated = True

    # TODO: Have the env mechanism generate the following env vars for
    #       each active sw entry ...
    #
    #       ENVR_SW_PATH_{sw} (path to install location)
    #       ENVR_SW_VER_{sw} (full version)
    #       ENVR_SW_VMAJOR_{sw} (major version only)
    #       ENVR_SW_VMINOR_{sw} (minor version only)
    #       ENVR_SW_VMM_{sw} (major minor versions compacted together,
    #                         no spaces)
    #       ENVR_SW_VBUILD_{sw} (build version only)
    #       ENVR_SW_VREV_{sw} (revision version only)

    def get_active_sw_env_spec(self):

        env_spec_list = []

        for sw_name in self.info_by_active_sw.keys():
            sw_info = self.info_by_active_sw[sw_name]
            sw_name_upper = sw_name.upper()

            env_spec_list.append({
                'var': 'ENVR_SW_%s__PATH' % sw_name.upper(), 
                'value': sw_info['install_location']
            })
            # DEBUG
            try:
                env_spec_list.append({
                    'var': 'ENVR_SW_%s__VER' % sw_name.upper(), 
                    'value': sw_info['version_info']['VER']
                })
            except:
                print('')
                print('sw_info: %s' % sw_info)
                print('')
                raise

            if not sw_info['is_dev_install']:
                # ver_part_key_list = ['MAJOR', 'MINOR', 'BUILD', 'REVISION']
                ver_part_key_list = ['MAJOR', 'MINOR']
                for ver_part_key in ver_part_key_list:
                    if ver_part_key in sw_info['version_info']:
                        env_spec_list.append({
                            'var': 'ENVR_SW_%s__V%s' % (sw_name_upper,
                                                       ver_part_key), 
                            'value': sw_info['version_info'][ver_part_key],
                        })
                # if 'MAJOR' in sw_info['version_info'] and \
                #         'MINOR' in sw_info['version_info']:
                #     mm_value = '%s%s' % (sw_info['version_info']['MAJOR'],
                #                         sw_info['version_info']['MINOR'])
                #     env_spec_list.append({
                #         'var':'ENVR_SW_%s__VMM' % sw_name.upper(), 
                #         'value': mm_value
                #     })

            # Find env spec JSON file ... first look at root of install
            # location for the given active sw ...
            env_spec_filepath = ('%s/envrunner_env.json' %
                                            sw_info['install_location'])
            if not os.path.isfile(env_spec_filepath):
                env_spec_filepath = None
                # fall back to central sw_envs
                try_spec_filename_list = [
                    '%s_%s_env.json' % (sw_name,
                                        sw_info['version_info']['VER']),
                    ('%s_%s_env.json' % (sw_name,
                                         sw_info['version_info']['MAJOR'])
                            if 'MAJOR' in sw_info['version_info']
                            else None),
                    '%s_env.json' % sw_name,
                ]
                for try_spec_filename in try_spec_filename_list:
                    try_spec_filepath = '%s/%s/%s' % (
                            os.getenv('ENVR_CFG_SW_ENVS_ROOT'),
                            sw_name, try_spec_filename)
                    if os.path.isfile(try_spec_filepath):
                        env_spec_filepath = try_spec_filepath
                        break

            if not env_spec_filepath:
                raise Exception('Unable to find env spec config file for '
                                'sw named "%s"' % sw_name)

            with open(env_spec_filepath, 'r') as env_spec_fp:
                env_spec_list += json.load(env_spec_fp)

        return env_spec_list

