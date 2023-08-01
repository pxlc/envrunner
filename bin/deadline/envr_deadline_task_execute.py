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


if __name__ == '__main__':

    job_id = os.getenv('ENVR_DEADLINE_JOBID')
    job_name = os.getenv('ENVR_DEADLINE_JOBNAME')

    job_submit_root = os.path.expandvars(
                                os.getenv('ENVR_DEADLINE_SUBMISSION_ROOT'))

    if not os.path.isdir(job_submit_root):
        raise Exception(
            'Job ID %s (job name "%s") can no longer access its job '
            'submission folder at: %s' % (job_id, job_name, job_submit_root))

    # Assumes that ENVR_PKG_PARENT_ROOT or ENVR_INSTALL_VERSIONS_ROOT is set
    # by the Deadline Job or set by user logon script
    #
    envrunner_pkg_parent_root = None
    envrunner_pkg_parent_root = os.getenv('ENVR_PKG_PARENT_ROOT')

    if not envrunner_pkg_parent_root:
        envrunner_install_versions_root = \
                os.getenv('ENVR_INSTALL_VERSIONS_ROOT')

        with open('%s/ACTIVE_VERSION' % envrunner_install_versions_root,
                'r') as in_fp:
            active_version = in_fp.read().strip()

        envrunner_pkg_parent_root = \
                os.path.join(envrunner_install_versions_root, active_version)

    # This code assumes that ENVR_CFG_ROOT is set in the environment. If it
    # is not then the envrunner config folder will be assumed to be at the
    # same level as top level envrunner software root (where various versions
    # of envrunner are contained within), requiring ENVR_INSTALL_VERSIONS_ROOT
    # to be set
    #
    if not os.getenv('ENVR_CFG_ROOT') and envrunner_pkg_parent_root:
        os.environ['ENVR_CFG_ROOT'] = ('%s_cfg' %
                                       envrunner_install_versions_root)

    # add the envrunner package parent path to sys.path
    sys.path.append(envrunner_pkg_parent_root)

    from envrunner.runner import run_launch_config

    project_code = os.getenv('ENVR_PROJECT_CODE')
    runner_cfg_filepath = '%s/envrunner_task_runner.json' % job_submit_root

    p_info = run_launch_config(project_code, runner_cfg_filepath)

    if p_info:
        p_info['process'].wait()

