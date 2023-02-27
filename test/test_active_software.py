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

sys.path.append('%s/../..' % os.path.dirname(os.path.abspath(__file__)))

ENVRUNNER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from envrunner.active_software import ActiveSoftwareSnapshot


if __name__ == '__main__':

    sw_defs_filepath = ('%s/envrunner_cfg/envrunner_site/'
                        'envrunner_sw_definitions.json' % ENVRUNNER_ROOT)

    prj_versions_filepath =  ('%s/envrunner_cfg/envrunner_projects/prj1/'
                              'prj1_sw_versions.json' % ENVRUNNER_ROOT)


    with open(sw_defs_filepath, 'r') as fp:
        sw_defs_d = json.load(fp)

    with open(prj_versions_filepath, 'r') as fp:
        prj_sw_versions_d = json.load(fp)

    a_sw_ss = ActiveSoftwareSnapshot(['maya', 'maya_usd'], sw_defs_d, 'prj1',
                                    prj_sw_versions_d)

    print('')
    print(':: Here is the Active Software ...')

    for sw_name in a_sw_ss.get_active_sw_names():
        version = a_sw_ss.get_sw_version(sw_name)
        install_path = a_sw_ss.get_install_path(sw_name)
        print('    %s (version %s) at %s' % (sw_name, version, install_path))

    print('')
    print('')

