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

from . import env_mechanism


def run_launch_config(prj_code, launch_cfg_filepath, detach_subprocess=False):

    envr_env, launch_cfg_d = env_mechanism.create_from_launch_config(
                                                prj_code, launch_cfg_filepath)
    p_info = None

    if detach_subprocess:
        p_info = envr_env.launch_subprocess(
                        launch_cfg_d.get('command'),
                        launch_cfg_d.get('args', []),
                        detach=detach_subprocess)
    else:
        # wait on subprocess using subprocess.check_call()
        envr_env.subprocess_check_call(launch_cfg_d.get('command'),
                                       launch_cfg_d.get('args', []))

    # NOTE: p_info will contain only one key, either "pid" (the process ID of
    #       the spawned process) or "process" (the subprocess.Popen object
    #       for the subprocess) ... p_info will be None if not detaching
    return p_info

