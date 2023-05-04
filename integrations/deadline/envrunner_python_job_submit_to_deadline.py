
import os
import json
import time
import getpass
import datetime
import subprocess


_THIS_DIR = os.path.basename(os.path.abspath(__file__))

# Deadline submission command line:
#
#   $ <deadlinecmd> <jobInfoFile> <pluginInfoFile> <pythonScriptToRun>
#

_USER = getpass.getuser()

_UNNAMED_JOB_NAME = ('[ENVRUNNER Python Job (UNNAMED) by %s]' %
                        getpass.getuser())

_ENVR_SUBMISSION_ROOT = os.path.expandvars(
                            '${ENVR_PIPELINE_DATA_ROOT}/farm_submissions')
_DEADLINE_CMD = os.path.expandvars(
                            '${DEADLINE_INSTALL_ROOT}/bin/deadlinecommand')

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
        'Version': 2.7
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


class ENVRPythonJobDeadlineSubmit(object):

    def __init__(self, project_code, runner_d,
                 job_params_d=None, plugin_params_d=None,
                 job_extra_env_vars_d=None, job_output_root=None,
                 specific_submission_root=None):

        # NOTE: if runner_json_d is provided then runner_filepath is ignored

        self.project_code = project_code
        self.runner_d = runner_d

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
            out_fp.write(json.dumps(self.runner_d, indent=4, sort_keys=True))
        
        # add in any job env vars to job info
        job_params_d = self.job_params_d.copy()

        extra_env_vars_d = {
            'ENVR_PROJECT_CODE': self.project_code,
            'ENVR_DEADLINE_SUBMISSION_ROOT': submit_folder_path
        }
        if self.job_extra_env_vars_d:
            extra_env_vars_d.update(self.job_extra_env_vars_d)

        env_key_list = sorted(extra_env_vars_d.keys())
        for env_idx, env_key in enumerate(env_key_list):
            job_params_d['EnvironmentKeyValue%s' % env_idx] = (
                                    self.job_extra_env_vars_d[env_key])

        # write out deadline job info config (write as .ini file)
        job_params_filepath = '%s/deadline_job_params.ini' % submit_folder_path
        with open(job_params_filepath, 'w') as out_fp:
            for job_param in sorted(job_params_d.keys()):
                out_fp.write('%s=%s\n' % (job_param, job_params_d[job_param]))

        # write out deadline plugin info config (write as .ini file)
        plugin_params_filepath = ('%s/deadline_plugin_params.ini' %
                                  submit_folder_path)

        with open(plugin_params_filepath, 'w') as out_fp:
            for plugin_param in sorted(self.plugin_params_d.keys()):
                out_fp.write('%s=%s\n' % (plugin_param,
                                          self.plugin_params_d[plugin_param]))

        cmd_and_args = [
            _DEADLINE_CMD,
            job_params_filepath,
            plugin_params_filepath,
        ]

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


if __name__ == '__main__':

    # def __init__(self, project_code, runner_d,
    #              job_params_d=None, plugin_params_d=None,
    #              job_extra_env_vars_d=None, job_output_root=None,
    #              specific_submission_root=None):

    # @@@ CONTINUE HERE!!!

    submission = ENVRPythonJobDeadlineSubmit('prj1',)
    pass

