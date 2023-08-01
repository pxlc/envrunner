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
import shlex
import getpass


_USER = getpass.getuser()


if __name__ == '__main__':

    project_code = sys.argv[1]

    session_spec_json_filepath = sys.argv[2]
    with open(session_spec_json_filepath, 'r') as in_fp:
        session_spec_d = json.load(in_fp)

    command_to_execute = sys.argv[3]
    command_args_list = shlex.split(sys.argv[4])
        # sys.argv[4] is all execution args in a single string

    job_params_d = {
        'Name': 'MIKE-TEST',
        'Pool': 'envrunner_test',
        'Frames': '1001',
        'ChunkSize': '4',
        'OverrideJobFailureDetection': 'True',
        'FailureDetectionJobErrors': '0',
        'OverrideTaskFailureDetection': 'True',
        'FailureDetectionTaskErrors': '1',

        # override the plugin name here if you are using your own fork
        # of the custom Deadline ENVRTaskRunner plugin or if you have
        # named the plugin with a version
        #
        'Plugin': 'ENVRTaskRunner',

        'MachineName': os.getenv('COMPUTERNAME') or os.getenv('HOSTNAME'),
        'UserName': _USER,
        'OutputDirectory0': '',

        # 'InitialStatus': 'Suspended',
    }

    plugin_params_d = {}
    job_extra_env_vars_d = {}
    job_output_root = None

    submission = ENVRJobDeadlineSubmit(
                    project_code, session_spec_d,
                    command_to_execute, command_args_list,
                    job_params_d=job_params_d,
                    plugin_params_d=plugin_params_d,
                    job_extra_env_vars_d=job_extra_env_vars_d,
                    job_output_root=job_output_root)

    submission.submit_to_deadline()

