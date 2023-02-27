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

ENVRUNNER_ROOT = '%s/..' % os.path.dirname(os.path.abspath(__file__))

sys.path.append('%s/..' % ENVRUNNER_ROOT)


from envrunner.env_mechanism import EnvRunnerEnv


if __name__ == '__main__':

    site_spec_list_file = (
        '%s/envrunner_cfg/site/site_env.json' % ENVRUNNER_ROOT)

    with open(site_spec_list_file, 'r') as fp:
        site_env_spec_list = json.load(fp)

    prj_code = 'prj1'

    prj_spec_list_file = (
        '%s/envrunner_cfg/projects/prj1/prj1_env.json' % ENVRUNNER_ROOT)

    with open(prj_spec_list_file, 'r') as fp:
        prj_env_spec_list = json.load(fp)

    prj_sw_versions_file = (
        '%s/envrunner_cfg/projects/prj1/prj1_sw_versions.json' % ENVRUNNER_ROOT)

    with open(prj_sw_versions_file, 'r') as fp:
        prj_sw_versions_d = json.load(fp)

    site_sw_defs_file = (
        '%s/envrunner_cfg/site/sw_definitions.json' % ENVRUNNER_ROOT)

    with open(site_sw_defs_file, 'r') as fp:
        site_sw_defs_d = json.load(fp)

    active_sw_list = ['maya', 'maya_usd']
    # active_sw_list = ['maya_usd'] # this will raise Exception - needs maya

    env_set = EnvRunnerEnv(active_sw_list, site_sw_defs_d, prj_code,
                           prj_sw_versions_d, site_env_spec_list,
                           prj_env_spec_list)
    print('')
    print(':: ENVR bootstrap env vars ...')
    print('')
    for k in sorted(os.environ.keys()):
        if k.startswith('ENVR_'):
            print('    %s = %s' % (k, os.getenv(k)))
    print('')
    print(':: SITE bootstrap env vars ...')
    print('')
    for k in sorted(os.environ.keys()):
        if k.startswith('SITE_'):
            print('    %s = %s' % (k, os.getenv(k)))
    print('')
    print(':: Launch environment ...')
    print('')
    print(json.dumps(env_set.get_env_d(), indent=4, sort_keys=True))
    print('')

