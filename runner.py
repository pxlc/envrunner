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

import json

from .env_mechanism import (
    EnvRunnerEnv,
    ENVR_CFG_SITE_ROOT,
    ENVR_CFG_PROJECTS_ROOT,
)


def run_launch_config(prj_code, launch_cfg_filepath, detach_subprocess=False):

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

        active_sw_list = launch_cfg_d['active_sw']
        extra_env_spec_list = launch_cfg_d.get('extra_env', [])

    envr_env = EnvRunnerEnv(active_sw_list, sw_defs_d, site_env_spec_list,
                            prj_code, prj_sw_versions_d, prj_env_spec_list,
                            extra_env_spec_list=extra_env_spec_list)

    p_info = envr_env.launch_subprocess(
                    launch_cfg_d.get('command'),
                    launch_cfg_d.get('args', []),
                    detach=detach_subprocess)

    # NOTE: p_info will contain only one key, either "pid" (the process ID of
    #       the spawned process) or "process" (the subprocess.Popen object
    #       for the subprocess)
    return p_info

