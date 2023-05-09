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
import getopt

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append('%s/../..' % THIS_DIR)

from envrunner.runner import run_launch_config


def usage():

    print('')
    print('  Usage: python %s [OPTIONS] <projectCode> <runnerCfgFilepath>' %
          os.path.basename(sys.argv[0]))

    print('')
    print('      OPTIONS')
    print('      -------')
    print('         -h | --help ... print this usage message and exit')
    print('         -d | --detach ... specify this flag if you want to detach')
    print('                           the child subprocess from the python')
    print('                           process.')
    print('')


if __name__ == '__main__':

    short_opt_str = 'hd'
    long_opt_list = ['help', 'detach']

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
        elif o in ('-d', '--detach'):
            detach_subprocess = True

    if len(args) != 2:
        print('')
        print('*** ERROR: expecting 2 arguments ... see usage below ...')
        usage()
        sys.exit(3)

    prj_code = args[0]
    runner_cfg_filepath = os.path.abspath(args[1])

    print('')
    print(':: Now running the following runner file for project "%s" ...' %
          prj_code)
    print('   ... runner cfg: %s' % runner_cfg_filepath)
    print('')

    p_info = run_launch_config(prj_code, runner_cfg_filepath,
                               detach_subprocess=detach_subprocess)

    # if not detaching then p_info will be None
    print('')
    print(':: p_info is %s' % p_info)
    print('')

