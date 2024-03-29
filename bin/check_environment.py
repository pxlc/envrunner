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
import sys
import json
import getopt

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append('%s/../..' % _THIS_DIR)

from envrunner.env_mechanism import (
    EnvRunnerEnv,
    ENVR_CFG_SITE_ROOT,
    ENVR_CFG_PROJECTS_ROOT,
)


def usage():

    print('')
    print('  Usage: python %s [OPTIONS] <projectCode> <runnerCfgFilepath>' %
          os.path.basename(sys.argv[0]))

    print('')
    print('      OPTIONS')
    print('      -------')
    print('         -h | --help ... print this usage message and exit')
    print('')


def print_env_details(prj_code, launch_cfg_filepath):

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
        site_sw_defs_d = json.load(fp)

    with open(launch_cfg_filepath, 'r') as fp:
        launch_cfg_d = json.load(fp)

    active_sw_list = launch_cfg_d['active_sw']

    extra_env_spec_list = launch_cfg_d.get('extra_env', [])

    envr_env = EnvRunnerEnv(active_sw_list, site_sw_defs_d, site_env_spec_list,
                            prj_code, prj_sw_versions_d, prj_env_spec_list,
                            extra_env_spec_list=extra_env_spec_list)
    print('')
    print('==== Env Spec List ==================================')
    envr_env.print_env_spec_list()

    print('')
    print('==== Applied Environment ============================')
    envr_env.print_applied_env()


if __name__ == '__main__':

    short_opt_str = 'h'
    long_opt_list = ['help']

    try:
        opts, args = getopt.getopt(sys.argv[1:], short_opt_str, long_opt_list)
    except getopt.GetoptError as err:
        print('')
        print(str(err))
        usage()
        sys.exit(2)

    prj_code = None
    runner_cfg_filepath = None
    detach_subprocess = False

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit(0)

    if len(args) != 2:
        print('')
        print('*** ERROR: expecting 2 arguments ... see usage below ...')
        usage()
        sys.exit(3)

    prj_code = args[0]
    runner_cfg_filepath = os.path.abspath(args[1])

    print_env_details(prj_code, runner_cfg_filepath)

