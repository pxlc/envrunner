
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

    # Assumes that ENVR_INSTALL_VERSIONS_ROOT is set by the Deadline Job or
    # set by user logon script
    envrunner_install_versions_root = os.getenv('ENVR_INSTALL_VERSIONS_ROOT')

    with open('%s/ACTIVE_VERSION' % envrunner_install_versions_root,
              'r') as in_fp:
        active_version = in_fp.read().strip()

    # This code assumes that the envrunner config folder is at same level as
    # top level envrunner software root (where various versions of envrunner
    # are contained within), unless ENVR_CFG_ROOT is already set in env
    #
    if not os.getenv('ENVR_CFG_ROOT'):
        os.environ['ENVR_CFG_ROOT'] = '%s_cfg' % envrunner_install_versions_root

    # add the active version of envrunner to sys.path
    sys.path.append('%s/%s' % (envrunner_install_versions_root, active_version))

    from envrunner.runner import run_launch_config

    project_code = os.getenv('ENVR_PROJECT_CODE')
    runner_cfg_filepath = '%s/envrunner_task_runner.json' % job_submit_root

    p_info = run_launch_config(project_code, runner_cfg_filepath)

    if p_info:
        p_info['process'].wait()

