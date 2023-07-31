
import os
import sys
import json
import time
import shlex
import getpass
import datetime
import subprocess

from envrunner.envr import get_sw_install
from envrunner.os_util import conform_path_slash


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Deadline submission command line:
#
#   $ <deadlinecmd> <jobInfoFile> <pluginInfoFile> <pythonScriptToRun>
#

_USER = getpass.getuser()

_UNNAMED_JOB_NAME = ('[ENVRUNNER Python Job (UNNAMED) by %s]' %
                        getpass.getuser())

# --- Environment variables that must be set in the submission environment ---
#
#   The following env vars must be set prior to executing a submission using
#   this code.
#
#   ENVR_USER_DATA_ROOT ... a root folder on the network to write envrunner
#                           user session data to, and also farm submission
#                           data to.
#
#   ENVR_CFG_ROOT ... the root folder path of the envrunner configuration
#                     files for your local site set up. This folder should
#                     be named `envrunner_cfg` for consistency and clarity.
#
#   ENVR_INSTALL_VERSIONS_ROOT ... versions of envrunner should be placed
#                              in a central network location under this
#                              structure:
#
#                              ${YOUR_CENTRAL_NETWORK_PATH}/envrunner/
#                                  0.1.16/
#                                      envrunner/
#                                  0.1.17/
#                                      envrunner/
#                                  ACTIVE_VERSION
#
#                              ... and this env var should be set to the root
#                              path of:
#
#                              ${YOUR_CENTRAL_NETWORK_PATH}/envrunner/
#
# ----------------------------------------------------------------------------

_ENVR_USER_DATA_ROOT = os.getenv('ENVR_USER_DATA_ROOT')
_ENVR_CFG_ROOT = os.getenv('ENVR_CFG_ROOT')
_ENVR_INSTALL_VERSIONS_ROOT = os.getenv('ENVR_INSTALL_VERSIONS_ROOT')

_ENVR_SUBMISSION_ROOT = '%s/farm_submissions' % _ENVR_USER_DATA_ROOT

_DEADLINE_CMD = '%s/bin/deadlinecommand' % get_sw_install('deadline')

_INITIAL_PARAMS = {
    'job_params':
    {
        'Name': _UNNAMED_JOB_NAME,
        'Pool': 'no_pool_assigned',
        'Frames': '1001',
        'ChunkSize': '4',
        'OverrideJobFailureDetection': 'True',
        'FailureDetectionJobErrors': '0',
        'OverrideTaskFailureDetection': 'True',
        'FailureDetectionTaskErrors': '1',
        'Plugin': 'ENVRPythonJob001',
        'MachineName': os.getenv('COMPUTERNAME') or os.getenv('HOSTNAME'),
        'UserName': _USER,
        'OutputDirectory0': '',
    },

    'plugin_params': {
        'Arguments': '',
        'Version': 3.7
    }
}


def _get_milliseconds_str():

    t = time.time()
    ms_i = int((t - float(int(t))) * 1000.0 + 0.5) % 1000

    return str(ms_i).zfill(3)


def load_json_file(json_filepath):

    try:
        with open(json_filepath, 'r') as in_fp:
            json_d = json.load(in_fp)
    except:
        print('>>')
        print('>>')
        print('>> Unable to load JSON file at: %s' % json_filepath)
        print('>>')
        print('>>')
        raise

    return json_d


class ENVRJobDeadlineSubmit(object):

    def __init__(self, project_code, session_spec_d,
                 command_to_execute, command_args_list,
                 job_params_d=None, plugin_params_d=None,
                 job_extra_env_vars_d=None, job_output_root=None,
                 specific_submission_root=None):

        # NOTE: if runner_json_d is provided then runner_filepath is ignored

        self.project_code = project_code
        self.session_spec_d = session_spec_d

        self.session_spec_d.update({
            'command': command_to_execute,
            'args': command_args_list,
            'active_sw': self.session_spec_d['full_active_sw_list'],
        })

        self.job_params_d = _INITIAL_PARAMS.get('job_params').copy()
        if job_params_d:
            self.job_params_d.update(job_params_d)

        self.plugin_params_d = _INITIAL_PARAMS.get('plugin_params').copy()
        if plugin_params_d:
            self.plugin_params_d.update(plugin_params_d)

        self.job_extra_env_vars_d = job_extra_env_vars_d
        self.job_output_root = job_output_root

        if specific_submission_root:
            self.submission_root = os.path.expandvars(specific_submission_root)
        else:
            self.submission_root = _ENVR_SUBMISSION_ROOT

    def submit_to_deadline(self):

        submit_dt_str = ('%s-%s' % (
                datetime.datetime.now().strftime('%Y%m%d-%H%M%S'),
                _get_milliseconds_str()))

        # build submission folder path
        submit_folder_path = '%s/%s/%s_submit_%s' % (
                             self.submission_root, _USER, _USER, submit_dt_str)

        os.makedirs(submit_folder_path)

        # write out envrunner format runner .json file
        runner_filepath = '%s/envrunner_task_runner.json' % submit_folder_path
        with open(runner_filepath, 'w') as out_fp:
            out_fp.write(json.dumps(self.session_spec_d,
                                    indent=4, sort_keys=True))
        
        # add in any job env vars to job info
        job_params_d = self.job_params_d.copy()

        extra_env_vars_d = {
            'ENVR_PROJECT_CODE': self.project_code,
            'ENVR_DEADLINE_SUBMISSION_ROOT': submit_folder_path,
            'ENVR_CFG_ROOT': _ENVR_CFG_ROOT,
            'ENVR_INSTALL_VERSIONS_ROOT': _ENVR_INSTALL_VERSIONS_ROOT,
        }
        if self.job_extra_env_vars_d:
            extra_env_vars_d.update(self.job_extra_env_vars_d)

        env_key_list = sorted(extra_env_vars_d.keys())
        for env_idx, env_key in enumerate(env_key_list):
            job_params_d['EnvironmentKeyValue%s' % env_idx] = ('%s=%s' %
                                        (env_key, extra_env_vars_d[env_key]))

        # write out deadline job info config (write as .ini file)
        job_params_filepath = '%s/deadline_job_info.ini' % submit_folder_path
        with open(job_params_filepath, 'w') as out_fp:
            for job_param in sorted(job_params_d.keys()):
                out_fp.write('%s=%s\n' % (job_param, job_params_d[job_param]))

        # write out deadline plugin info config (write as .ini file)
        plugin_params_filepath = ('%s/deadline_plugin_info.ini' %
                                  submit_folder_path)

        with open(plugin_params_filepath, 'w') as out_fp:
            for plugin_param in sorted(self.plugin_params_d.keys()):
                out_fp.write('%s=%s\n' % (plugin_param,
                                          self.plugin_params_d[plugin_param]))

        farm_worker_execution_script = conform_path_slash(
            '%s/../bin/deadline/envr_deadline_task_execute.py' % _THIS_DIR)

        cmd_and_args = [
            _DEADLINE_CMD, '-SubmitMultipleJobs', '-job',
            job_params_filepath,
            plugin_params_filepath,
            farm_worker_execution_script,  # this gets uploaded to deadline
        ]

        TEST_ONLY = False

        if TEST_ONLY:
            print('')
            print(':: submit folder path: %s' % submit_folder_path)
            print('')
            print(':: Test only ... would be executing: %s' % cmd_and_args)
            print('')
        else:
            p = subprocess.Popen(cmd_and_args,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = p.communicate()

            if out:
                print('')
                print(out.decode('utf-8'))

            if err:
                print('')
                print(err.decode('utf-8'))

            print('')
            print(':: Deadline submission executed. cmd_and_args: %s' %
                        cmd_and_args)
            print('')
            print(':: submit folder path: %s' % submit_folder_path)
            print('')


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
        'Plugin': 'ENVRPythonJob_v001',
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
