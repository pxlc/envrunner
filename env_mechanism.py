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
import sys
import json
import time
import getpass
import datetime
import subprocess

from .os_util import (
    os_info, fslash, conform_path_slash, reset_bootstrap_env,
    ENVR_CFG_ROOT, ENVR_CFG_SITE_ROOT, ENVR_CFG_PROJECTS_ROOT,
    ENVR_CFG_SW_ENVS_ROOT
)
from .active_software import ActiveSoftwareSnapshot


if sys.version_info.major > 2:
    unicode = str


_ENVRUNNER_PARENT_DIR = os.path.dirname(os.path.dirname(
                                            os.path.abspath(__file__)))
EMBEDDED_VAR_PATTERN = r'\${[A-Za-z0-9_]+}'


def get_all_embedded_vars(input_str):

    try:
        embedded_var_list = [ev[2:-1] for ev in
                                re.findall(EMBEDDED_VAR_PATTERN, input_str)]
    except:
        print('>>>')
        print('>>>')
        print('>>> In env_mechanism.get_all_embedded_vars() ...')
        print('>>>   ERROR parsing string "%s"' % input_str)
        print('>>>')
        print('>>>')
        raise

    return embedded_var_list


def get_user_session_info():

    all_users_sessions_root = os.getenv('ENVR_ALL_USERS_SESSIONS_ROOT')
    if not all_users_sessions_root:
        envr_user_data_root = os.getenv('ENVR_ALL_USERS_DATA_ROOT')
        if envr_user_data_root:
            all_users_sessions_root = os.path.join(envr_user_data_root,
                                                   'envr_user_sessions')
        else:
            # fallback to standard temp locations
            if os_info.os == 'windows':
                all_users_sessions_root = (os.path.join(
                    os.path.expandvars('$USERPROFILE'),
                    'AppData', 'Local', 'Temp',
                    '__ENVRUNNER_USER_SESSIONS'
                ))
            elif os_info.os == 'macos':
                all_users_sessions_root = '/var/tmp/__ENVRUNNER_USER_SESSIONS'
            else:
                all_users_sessions_root = '/usr/tmp/__ENVRUNNER_USER_SESSIONS'

    t = time.time()
    time_ms_str = str(int((t - float(int(t))) * 1000.0) % 1000).zfill(3)
    session_ts_str = '%s.%s' % (
                        datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'),
                        time_ms_str)
    session_day_date_str = session_ts_str.split('_')[0]

    user_session_day_dirpath = '%s/%s/%s' % (all_users_sessions_root,
                                             getpass.getuser(),
                                             session_day_date_str)
    if not os.path.isdir(user_session_day_dirpath):
        os.makedirs(user_session_day_dirpath)

    return {
        'user': getpass.getuser(),
        'session_ts_str': session_ts_str,
        'user_session_day_dirpath': user_session_day_dirpath,
    }


def _load_configs(prj_code):

    site_spec_list_file = '%s/site_env.json' % ENVR_CFG_SITE_ROOT
    with open(site_spec_list_file, 'r') as fp:
        site_env_spec_list = json.load(fp)

    prj_spec_list_file = (
        '%s/%s/%s_env.json' % (ENVR_CFG_PROJECTS_ROOT, prj_code, prj_code))
    with open(prj_spec_list_file, 'r') as fp:
        prj_env_spec_list = json.load(fp)

    prj_sw_versions_file = (
        '%s/%s/%s_sw_versions.json' % (
                            ENVR_CFG_PROJECTS_ROOT, prj_code, prj_code))
    with open(prj_sw_versions_file, 'r') as fp:
        prj_sw_versions_d = json.load(fp)

    site_sw_defs_file = '%s/sw_definitions.json' % ENVR_CFG_SITE_ROOT
    with open(site_sw_defs_file, 'r') as fp:
        sw_defs_d = json.load(fp)

    return (
        site_env_spec_list, prj_env_spec_list, prj_sw_versions_d, sw_defs_d)


def create_env(prj_code, active_sw_list, extra_env_spec_list=None):

    (site_env_spec_list, prj_env_spec_list,
        prj_sw_versions_d, sw_defs_d) = _load_configs(prj_code)

    envr_env = EnvRunnerEnv(active_sw_list, sw_defs_d, site_env_spec_list,
                            prj_code, prj_sw_versions_d, prj_env_spec_list,
                            extra_env_spec_list=extra_env_spec_list)
    return envr_env


def create_from_launch_config(prj_code, launch_cfg_filepath):

    # We first load the launch config (runner .json file) and see if it
    # has a session spec ... session spec is processed differently
    with open(launch_cfg_filepath, 'r') as fp:
        launch_cfg_d = json.load(fp)

    if 'session_spec' in launch_cfg_d:
        session_spec_d = launch_cfg_d['session_spec']
        site_env_spec_list = session_spec_d['site_env_spec_list']
        prj_env_spec_list = session_spec_d['prj_env_spec_list']
        prj_sw_versions_d = session_spec_d['prj_sw_versions_d']
        sw_defs_d = session_spec_d['active_sw_defs_d']
        active_sw_list = session_spec_d['full_active_sw_list']
        extra_env_spec_list = session_spec_d['extra_env_spec_list']
    else:
        (site_env_spec_list, prj_env_spec_list,
            prj_sw_versions_d, sw_defs_d) = _load_configs(prj_code)

        active_sw_list = launch_cfg_d['active_sw']
        extra_env_spec_list = launch_cfg_d.get('extra_env', [])

    envr_env = EnvRunnerEnv(active_sw_list, sw_defs_d, site_env_spec_list,
                            prj_code, prj_sw_versions_d, prj_env_spec_list,
                            extra_env_spec_list=extra_env_spec_list)

    return (envr_env, launch_cfg_d)


class EnvRunnerEnv(object):

    def __init__(self, active_sw_list, sw_defs_d, site_env_spec_list,
                 prj_code, prj_sw_versions_d, prj_env_spec_list,
                 extra_env_spec_list=None, path_slash=None):

        reset_bootstrap_env()

        self.path_slash = path_slash if path_slash is not None else os.sep
        self.opposite_path_slash = '\\' if self.path_slash == '/' else '/'

        if self.path_slash not in ('\\', '/'):
            raise Exception('Invalid path slash character provided: "%s"' %
                            self.path_slash)

        self.prj_code = prj_code
        self.prj_sw_versions_d = prj_sw_versions_d
        self.sw_defs_d = sw_defs_d

        self.site_env_spec_list = site_env_spec_list
        self._bootstrap_site_env()

        self.active_sw_list = active_sw_list

        # for active_sw_set, we just want the names of the active software
        # packages, so need to strip any entries that have the "@" symbol,
        # indicating an override version or override dev path
        #
        self.active_sw_set = set([a_sw.split('@')[0] for a_sw in
                                    self.active_sw_list])

        self.user_session_info = get_user_session_info()
        self.user_current_session_root = os.path.join(
                    self.user_session_info.get('user_session_day_dirpath'),
                    self.user_session_info.get('session_ts_str'))
        if not os.path.isdir(self.user_current_session_root):
            os.makedirs(self.user_current_session_root)

        self.session_spec_file = os.path.join(
                    self.user_current_session_root,
                    '%s_%s_envrunner_session_spec.json' % (
                            self.user_session_info.get('session_ts_str'),
                            self.user_session_info.get('user')))

        session_spec_d = {
            '__type__': 'session_spec',
            'project_code': prj_code,
            'full_active_sw_list': active_sw_list[:],
            'active_sw_name_list': sorted(list(self.active_sw_set)),
            'site_env_spec_list': site_env_spec_list[:],
            'prj_env_spec_list': prj_env_spec_list[:],
            'extra_env_spec_list': extra_env_spec_list[:]
                                        if extra_env_spec_list else [],
            'prj_sw_versions_d': prj_sw_versions_d.copy(),
            'active_sw_defs_d': {k: sw_defs_d[k] for k in sw_defs_d.keys()
                                                if k in self.active_sw_set},
            'session_spec_file': self.session_spec_file,
        }

        with open(self.session_spec_file, 'w') as out_fp:
            out_fp.write('%s\n' %
                    json.dumps(session_spec_d, indent=4, sort_keys=True))

        self.active_sw_snapshot = ActiveSoftwareSnapshot(
                                        self.active_sw_list,
                                        self.sw_defs_d,
                                        self.prj_code,
                                        self.prj_sw_versions_d)

        sw_env_spec_list = self.active_sw_snapshot.get_active_sw_env_spec()

        prj_spec = {'var': 'ENVR_PRJ_CODE', 'value': self.prj_code}
        envr_session_spec = {
            'single_path': 'ENVR_SESSION_SPEC_FILE',
            'value': self.session_spec_file,
        }

        self.prj_env_spec_list = prj_env_spec_list

        if extra_env_spec_list is None:
            extra_env_spec_list = []

        self.env_spec_list = self._flatten_spec_list([prj_spec] +
                                                     [envr_session_spec] +
                                                     site_env_spec_list +
                                                     sw_env_spec_list +
                                                     prj_env_spec_list +
                                                     extra_env_spec_list)
        self.resulting_env_d = None

        self.env_var_names = None
        self.info_by_env_var = None
        self.has_embedded_by_env_var = None

        self._process_spec_list()

    def _bootstrap_site_env(self):

        for site_spec in self.site_env_spec_list:
            if type(site_spec) is not dict:
                continue # skip comments in string entries

            # Mark the spec with "site": True
            site_spec["site"] = True

            if 'SKIP' in site_spec and site_spec['SKIP']:
                # mechanism to disable an entry yet keep it around for reference
                continue

            if 'DELETE_ENV_VAR' in site_spec and site_spec['DELETE_ENV_VAR']:
                env_var = None
                if 'var' in site_spec:
                    env_var = site_spec['var']
                elif 'single_path' in site_spec:
                    env_var = site_spec['single_path']
                elif 'path' in site_spec:
                    env_var = site_spec['path']
                else:
                    raise Exception('Unknown Site spec format - spec: %s' %
                                    site_spec)
                if env_var in os.environ:
                    del os.environ[env_var]

            elif 'var' in site_spec or 'single_path' in site_spec:
                spec_var = (site_spec['var'] if 'var' in site_spec
                                             else site_spec['single_path'])
                spec_value = site_spec['value']
                if type(spec_value) is dict:
                    spec_value = self._get_os_specific_value_from_dict(
                                                        spec_var, spec_value)
                if 'single_path' in site_spec:
                    os.environ[spec_var] = conform_path_slash(
                                                os.path.expandvars(spec_value),
                                                self.path_slash)
                else:
                    os.environ[spec_var] = spec_value

            elif 'path' in site_spec:
                path_value_d = site_spec['value']
                path_var = site_spec['path']
                mode = site_spec['mode']
                path_value = os.path.expandvars(
                    self._get_path_value_from_path_spec(path_value_d, path_var))
                if mode == 'pre':
                    os.environ[path_var] = os.pathsep.join([
                                            path_value, os.environ[path_var]])
                elif mode == 'post':
                    os.environ[path_var] = os.pathsep.join([
                                            os.environ[path_var], path_value])
                elif mode == 'overwrite':
                    os.environ[path_var] = path_value

                elif mode == 'remove':
                    # NOTE: this is a Site spec list feature only!
                    filtered_list = []

                    current_list = os.environ[path_var].split(os.pathsep)
                    remove_list = path_value.split(os.pathsep)

                    for curr_path in current_list:
                        if curr_path in remove_list:
                            continue
                        filtered_list.append(curr_path)

                    os.environ[path_var] = os.pathsep.join(filtered_list)
                else:
                    raise Exception(
                            'Unknown path mode, "%s", in Site spec list, '
                            'spec is: %s' % (mode, site_spec))
            else:
                raise Exception(
                    'Unknown Site spec dictionary format: %s' % site_spec)

    def _get_os_specific_value_from_dict(self, env_var, spec_value_d):

        specific_value = None
        for os_specificity in os_info.specificity_list:
            if os_specificity in spec_value_d:
                specific_value = spec_value_d[os_specificity]
                break
            if not specific_value and '_all' in spec_value_d:
                specific_value = spec_value_d['_all']
        if not specific_value:
            raise Exception(
                'Value not found for local OS for env var "%s"' % env_var)
        return specific_value

    def _flatten_spec_list(self, env_spec_list):

        # remove comments (str entries) and flatten groups
        result_spec_list = []
        for spec in env_spec_list:
            if type(spec) is not dict:
                continue  # remove comments
            if 'SKIP' in spec and spec['SKIP']:
                # a mechanism to deactivate an env spec yet still
                # keep it in # the env config for reference ... entry
                # will be skipped if # 'SKIP' key is found and its
                # value is truthy (e.g. True, 1, etc.)
                continue
            if 'group' in spec:
                required_set = set(spec.get('requires'))
                if not required_set.issubset(self.active_sw_set):
                    continue
                group_spec_list = spec.get('spec_list')
                for group_spec in group_spec_list:
                    if type(group_spec) is not dict:
                        continue # remove comments
                    if 'SKIP' in spec and spec['SKIP']:
                        # a mechanism to deactivate an env spec yet still
                        # keep it in # the env config for reference ... entry
                        # will be skipped if # 'SKIP' key is found and its
                        # value is truthy (e.g. True, 1, etc.)
                        continue
                    if 'group' in group_spec:
                        raise Exception('Nested group specs are not allowed.')
                    result_spec_list.append(group_spec)
            else:
                result_spec_list.append(spec)

        return result_spec_list

    def _get_path_value_from_path_spec(self, path_value_d, path_var):

        distro_key = '%s/%s' % (os_info.os, os_info.distro)
        version_key = '%s/%s/%s' % (os_info.os, os_info.distro,
                                    os_info.version)
        path_value = None

        if version_key in path_value_d:
            path_value = os.pathsep.join(path_value_d[version_key])
        elif distro_key in path_value_d:
            path_value = os.pathsep.join(path_value_d[distro_key])
        elif os_info.os in path_value_d:
            path_value = os.pathsep.join(path_value_d[os_info.os])
        elif '_all' in path_value_d:
            path_value = os.pathsep.join(path_value_d['_all'])
        else:
            # TODO: Warn user that no value was found for this spec
            raise Exception('No value found for path: %s' % path_var)

        return path_value

    def _process_spec_list(self):

        self.env_var_names = []
        self.info_by_env_var = {}
        self.has_embedded_by_env_var = {}

        for spec in self.env_spec_list:
            # skip comment entries (anything that is a string)
            if type(spec) in (str, unicode):
                continue

            if 'site' in spec:
                # These have already been applied to os.environ
                # in a site bootstrapping phase, so skip
                continue

            if 'var' in spec or 'single_path' in spec:
                # handle straight env var assignment ... values may still
                # contain embedded env vars
                env_var = spec.get('var') if 'var' in spec \
                                          else spec.get('single_path')
                env_value = spec.get('value')
                is_single_path = 'single_path' in spec

                if type(env_value) is dict:
                    env_value = self._get_os_specific_value_from_dict(
                                                        env_var, env_value)
                elif type(env_value) in (int, float, bool):
                    env_value = str(env_value)

                embedded_vars = get_all_embedded_vars(env_value)
                self.info_by_env_var[env_var] = {
                    'value': env_value,
                    'type': 'single_path' if is_single_path else 'var',
                }
                if len(embedded_vars):
                    self.has_embedded_by_env_var[env_var] = True
                else:
                    self.has_embedded_by_env_var.pop(env_var, None)

                if env_var not in self.env_var_names:
                    self.env_var_names.append(env_var)

            elif 'path' in spec:

                path_value_d = spec['value']
                path_var = spec['path']
                mode = spec['mode']

                path_value = self._get_path_value_from_path_spec(path_value_d,
                                                                 path_var)
                if path_var not in self.info_by_env_var:
                    self.info_by_env_var[path_var] = {
                        'type': 'path',
                        'spec_list': [],
                    }

                self.info_by_env_var[path_var]['spec_list'].append({
                    'value': path_value, 'mode': mode,
                })

                if path_var not in self.env_var_names:
                    self.env_var_names.append(path_var)

            else:
                raise Exception('Unsupported spec entry: %s' % spec)

        # Now evaluate embedded env vars in values in var or single_path
        # type spec entries ...
        count = 1
        while len(self.has_embedded_by_env_var) and count < 6:
            for var_name in self.env_var_names:
                info_d = self.info_by_env_var[var_name]

                if info_d['type'] in ('var', 'single_path'):
                    resulting_value, still_has_embedded = \
                        self._expand_vars(info_d['value'])
                    info_d['value'] = resulting_value

                    if still_has_embedded:
                        self.has_embedded_by_env_var[var_name] = True
                    else:
                        self.has_embedded_by_env_var.pop(var_name, None)
            count += 1

        # Now expand embedded vars in path values
        for var_name in self.env_var_names:
            info_d = self.info_by_env_var[var_name]
            if info_d['type'] != 'path':
                continue
            for spec in info_d['spec_list']:
                new_value, still_has_embedded = self._expand_vars(
                                                        spec['value'])
                spec['value'] = new_value

        # Now evaluate environment
        self.resulting_env_d = {}

        for var_name in self.env_var_names:
            info_d = self.info_by_env_var[var_name]
            if info_d['type'] == 'path':
                path_str = os.getenv(var_name, '')
                for spec in info_d['spec_list']:
                    if spec['mode'] == 'pre':
                        path_str = (
                            '%s%s%s' % (spec['value'], os.pathsep, path_str)
                            if path_str else spec['value'])
                    elif spec['mode'] == 'post':
                        path_str = (
                            '%s%s%s' % (path_str, os.pathsep, spec['value'])
                            if path_str else spec['value'])
                    elif spec['mode'] == 'overwrite':
                        path_str = spec["value"]
                    else:
                        raise Exception('Unknown path mode: "%s"' %
                                        spec['mode'])
                # opporunity here to do any path processing like forcing
                # slashes a particular way
                self.resulting_env_d[var_name] = conform_path_slash( 
                                                        path_str,
                                                        self.path_slash)
            elif info_d['type'] == 'single_path':
                # opporunity here to do any path processing like forcing
                # slashes a particular way
                self.resulting_env_d[var_name] = conform_path_slash(
                                                        info_d['value'],
                                                        self.path_slash)
            elif info_d['type'] == 'var':
                self.resulting_env_d[var_name] = info_d['value']

    def _expand_vars(self, value_str):

        still_has_embedded = False
        embedded_vars = get_all_embedded_vars(value_str)
        for embed_var in embedded_vars:
            if embed_var in self.env_var_names:
                if self.has_embedded_by_env_var.get(embed_var, False):
                    still_has_embedded = True
                    continue

                embed_value = self.info_by_env_var[embed_var].get('value')
                if type(embed_value) in (str, unicode):
                    value_str = value_str.replace('${%s}' % embed_var,
                                                  embed_value)
                else:
                    still_has_embedded = True
            else:
                # then look for the var in current environment
                os_env_value = os.getenv(embed_var)
                if os_env_value:
                    value_str = value_str.replace('${%s}' % embed_var,
                                                  os_env_value)

        return (value_str, still_has_embedded)

    def get_env_spec_list(self):

        return self.env_spec_list

    def get_env_d(self):

        return self.resulting_env_d

    def apply_to_os_env(self):

        for env_var in self.resulting_env_d.keys():
            os.environ[str(env_var)] = str(self.resulting_env_d[env_var])

        # always add access to envrunner package so envr module is available
        # for convenience functionality
        os.environ['PYTHONPATH'] = (
            '%s%s%s' % (_ENVRUNNER_PARENT_DIR, os.pathsep,
                        os.getenv('PYTHONPATH'))
                if 'PYTHONPATH' in os.environ else _ENVRUNNER_PARENT_DIR)

        # be sure to also inject the session's raw active sw list
        os.environ['ENVR_ACTIVE_SW_LIST'] = ';'.join(self.active_sw_list)

        # inject the user current session root path into environment
        os.environ['ENVR_USER_CURRENT_SESSION_ROOT'] = \
            self.user_current_session_root

    def copy_of_current_os_env(self):

        return os.environ.copy()

    def restore_os_env(self, bkup_of_os_env_d):

        os.environ.data = bkup_of_os_env_d.copy()

    def launch_by_os_system_call(self, os_system_call_str):

        orig_env_to_restore_d = self.copy_of_current_os_env()
        self.apply_to_os_env()

        os.system(os_system_call_str)

        # restore the environment
        self.restore_os_env(orig_env_to_restore_d)

    def _launch_subprocess(self, subproc_cmd, subproc_args, creation_flags=0,
                           shell=False, stdin=None, stdout=None, stderr=None,
                           cwd=None, detach=False):

        orig_env_to_restore_d = self.copy_of_current_os_env()
        self.apply_to_os_env()

        cmd_and_args = [os.path.expandvars(item)
                            for item in ([subproc_cmd] + subproc_args)]

        if detach:
            if os_info.os == 'windows':
                # NOTE: the following works on Windows, with python run in
                #       Powershell, to detach the process ...

                # creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
                creation_flags = subprocess.CREATE_NEW_CONSOLE
                shell = True
            else:
                if sys.version_info.major >= 3:
                    p = subprocess.Popen(cmd_and_args, shell=shell,
                                         cwd=cwd, stdin=stdin, stdout=stdout,
                                         stderr=stderr, start_new_session=True,
                                         creationflags=creation_flags)
                    # restore the environment
                    self.restore_os_env(orig_env_to_restore_d)
                    return {'pid': p.pid}
                else:
                    # Do nothing ... in Python 2.7 on linux, just don't call
                    # .wait() or # .communicate() or .poll() on resulting
                    # Popen object # for it to fork to another process?
                    pass

        p = subprocess.Popen(cmd_and_args, shell=shell, cwd=cwd,
                             stdin=stdin, stdout=stdout, stderr=stderr,
                             creationflags=creation_flags)

        # restore the environment
        self.restore_os_env(orig_env_to_restore_d)

        if detach:
            return {'pid': p.pid}
        else:
            return {'process': p}

    def subprocess_check_call(self, cmd, arg_list):

        orig_env_to_restore_d = self.copy_of_current_os_env()
        self.apply_to_os_env()

        cmd_and_args = [os.path.expandvars(item)
                            for item in ([cmd] + arg_list)]

        try:
            subprocess.check_call(cmd_and_args)
        except:
            print('>>>')
            print('>>>')
            print('>>> ERROR: EnvRunnerEnv.subprocess_check_call() method '
                  'unable to create subprocess. Here are the command and '
                  'arguments used ...')
            for item in cmd_and_args:
                print('   %s' % item)
            print('>>>')
            print('>>> PATH is ...')
            for p in os.getenv('PATH').split(os.pathsep):
                print('   %s' % p)
            print('>>>')
            print('>>>')
            raise

        # restore the environment
        self.restore_os_env(orig_env_to_restore_d)

    def launch_subprocess(self, subproc_cmd, subproc_args, creation_flags=0,
                           shell=False, stdin=None, stdout=None, stderr=None,
                           cwd=None, detach=False):
        try:
            p_info = self._launch_subprocess(
                                subproc_cmd, subproc_args,
                                creation_flags=creation_flags,
                                shell=shell, stdin=stdin, stdout=stdout,
                                stderr=stderr, cwd=cwd, detach=detach)
        except:
            print('')
            print('------------------------------------------------------')
            print('>>> ERROR occurred attempting to launch subprocess ...')
            print('          > command: %s' % subproc_cmd)
            print('          > args: %s' % subproc_args)
            print('          > PATH (env var) ...')
            for p in os.getenv('PATH').split(os.pathsep):
                if p.strip():
                    print('                  %s' % p)
            print('------------------------------------------------------')
            print('')
            raise

        return p_info

    def print_env_spec_list(self):

        print('')
        print(json.dumps(self.env_spec_list, indent=4, sort_keys=True))
        print('')

    def print_applied_env(self):

        orig_env_to_restore_d = self.copy_of_current_os_env()
        self.apply_to_os_env()

        for evar in sorted(os.environ.keys()):
            if 'PATH' in evar:
                print('')
                print(':: %s ...' % evar)
                print('')
                for path in os.getenv(evar).split(os.pathsep):
                    if path.strip():
                        print('    %s' % path.strip())
            else:
                print('')
                print(':: %s = %s' % (evar, os.getenv(evar)))

        print('')

        # restore the environment
        self.restore_os_env(orig_env_to_restore_d)

    # ------------------------------------------------------------------------
    #
    #  Provide API to internal ActiveSoftwareSnapshot object
    #
    # ------------------------------------------------------------------------
    def get_active_sw_names(self):

        return self.active_sw_snapshot.get_active_sw_names()

    def get_sw_install_path(self, sw_name):

        return self.active_sw_snapshot.get_sw_install_path(sw_name)

    def get_sw_info(self, sw_name):

        return self.active_sw_snapshot.get_sw_info(sw_name)

    def get_sw_version(self, sw_name):

        return self.active_sw_snapshot.get_sw_version(sw_name)

    def get_sw_version_info(self, sw_name):

        return self.active_sw_snapshot.get_sw_version_info(sw_name)

    def is_sw_dev_installed(self, sw_name):

        return self.active_sw_snapshot.is_sw_dev_installed(sw_name)

