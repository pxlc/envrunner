
import os
import sys
import json

from Deadline.Plugins import *
from Deadline.Scripting import *


def GetDeadlinePlugin():

    return ENVRTaskRunnerJobPlugin()


def CleanupDeadlinePlugin( deadlinePlugin ):

    deadlinePlugin.Cleanup()


class ENVRTaskRunnerJobPlugin(DeadlinePlugin):

    def __init__( self ):

        self.InitializeProcessCallback += self.InitializeProcess
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup(self):

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.PreRenderTasksCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):

        self.PluginType = PluginType.Simple
        self.SingleFramesOnly = False
        self.StdoutHandling = True

        job = self.GetJob()
        extra_info_dict = job.ExtraInfoDictionary
        d = {key: extra_info_dict.get_Item(key)
                    for key in extra_info_dict.get_Keys()}
        self.SetEnvironmentVariable("ENVR_DEADLINE_JOBINFO_EXTRAINFOKEYVALUES",
                                    json.dumps(d, sort_keys=True) )

        stdout_handlers_d = {}

        if 'StdoutHandlersJsonFile' in d:
            json_filepath = os.path.expandvars(d['StdoutHandlersJsonFile'])
            with open(json_filepath, 'r') as in_fp:
                stdout_handlers_d = json.load(in_fp)

        self.AddStdoutHandlerCallback(
            "^((.*)(WARNING|Warning)(.*))$").HandleCallback += \
                    self.HandleStdoutWarning

        if 'WarningRegexList' in stdout_handlers_d:
            regex_str_list = stdout_handlers_d['WarningRegexList']
            for regex_str in regex_str_list:
                self.AddStdoutHandlerCallback(regex_str).HandleCallback += \
                    self.HandleStdoutWarning

        # #---- Original code left here for reference ---------------
        # self.AddStdoutHandlerCallback(
        #     "ERROR:(.*)" ).HandleCallback += self.HandleStdoutError
        # #----------------------------------------------------------

        self.AddStdoutHandlerCallback(
            "Exception: (.*)" ).HandleCallback += self.HandleStdoutError

        self.AddStdoutHandlerCallback(
            "SyntaxError: (.*)" ).HandleCallback += self.HandleStdoutError

        if 'ErrorRegexList' in stdout_handlers_d:
            regex_str_list = stdout_handlers_d['ErrorRegexList']
            for regex_str in regex_str_list:
                self.AddStdoutHandlerCallback(regex_str).HandleCallback += \
                    self.HandleStdoutError

        # Progress handling
        a_of_b_progress_pattern = r'Progress: .* \(([0-9]+) of ([0-9]+)\)'
        self.AddStdoutHandlerCallback(
            a_of_b_progress_pattern).HandleCallback += self.HandleProgressAofB

        percent_progress_pattern = \
                        r'Progress: .* \([0-9]{1,3}(\.[0-9]+){0,1}%\)'
        self.AddStdoutHandlerCallback(
            percent_progress_pattern).HandleCallback += \
                self.HandleProgressPercent

    ## Called by Deadline for each task the Slave renders.
    def PreRenderTasks(self):

        job = self.GetJob()

        self.SetEnvironmentVariable("ENVR_DEADLINE_JOBID", job.JobId)
        self.SetEnvironmentVariable("ENVR_DEADLINE_JOBNAME", job.JobName)

        task = self.GetCurrentTask()

        self.SetEnvironmentVariable("ENVR_DEADLINE_TASKSTARTTIME",
                                    str(task.TaskStartTime) )
        # NOTE: TaskStartTime is of type <class 'System.DateTime'> and when cast to string is in this format "MM/DD/YYYY HH:MM:SS"

        self.SetEnvironmentVariable("ENVR_DEADLINE_STARTFRAME",
                                    str(self.GetStartFrame()))
        self.SetEnvironmentVariable("ENVR_DEADLINE_ENDFRAME",
                                    str(self.GetEndFrame()))
        self.SetEnvironmentVariable("ENVR_DEADLINE_NUMFRAMES", 
                        str(self.GetEndFrame() - self.GetStartFrame() + 1))

        self.SetEnvironmentVariable("ENVR_DEADLINE_WORKERNAME",
                                    str(self.GetSlaveName()))
        self.SetEnvironmentVariable("ENVR_DEADLINE_TASKID",
                                    str(self.GetCurrentTaskId()))

        cpu_affinity_str = \
                str([c for c in self.CpuAffinity()])[1:-1].replace(' ','')
        gpu_affinity_str = \
                str([g for g in self.GpuAffinity()])[1:-1].replace(' ','')

        self.SetEnvironmentVariable("ENVR_DEADLINE_CPUAFFINITY",
                                    '%s' % cpu_affinity_str)
        self.SetEnvironmentVariable("ENVR_DEADLINE_GPUAFFINITY",
                                    '%s' % gpu_affinity_str)

    def RenderExecutable(self):

        version = self.GetPluginInfoEntry("Version")

        exeList = self.GetConfigEntry("Python_Executable_" +
                                      version.replace( ".", "_" ))

        exe = FileUtils.SearchFileList(exeList)
        if exe == "":
            self.FailRender("Python " + version + " executable was not found "
                            "in the semicolon separated list \"" + exeList +
                            "\". The path to the render executable can be "
                            "configured from the Plugin Configuration in the "
                            "Deadline Monitor.")

        return exe

    def RenderArgument(self):

        scriptFile = self.GetPluginInfoEntryWithDefault("ScriptFile",
                                                    self.GetDataFilename() )
        scriptFile = RepositoryUtils.CheckPathMapping(scriptFile)

        arguments = self.GetPluginInfoEntryWithDefault("Arguments", "")
        arguments = RepositoryUtils.CheckPathMapping(arguments)

        return "\"" + scriptFile + "\" " + arguments

    ## Callback for when a line of stdout contains a WARNING message.
    def HandleStdoutWarning(self):
        self.LogWarning(self.GetRegexMatch(0))

    ## Callback for when a line of stdout contains an ERROR message.
    def HandleStdoutError(self):
        self.LogStdout('>> ENVRTaskRunner ERROR >> %s' % self.GetRegexMatch(0))
        self.FailRender("Detected an error: " + self.GetRegexMatch(0))

    def HandleProgressAofB(self):
        line = self.GetRegexMatch(0)
        self.LogWarning(line)

        tmp_str = line.replace('(', '###').replace(')', '###')
        self.LogWarning(tmp_str)

        tmp2_str = tmp_str.split('###')[-2]
        self.LogWarning(tmp2_str)

        (a, b) = [int(s) for s in tmp2_str.split(' of ')]
        progress_f = (float(a) / float(b)) * 100.0

        self.SetProgress(progress_f)

    def HandleProgressPercent(self):
        line = self.GetRegexMatch(0)

        tmp_str = line.replace('(', '###').replace(')', '###').split('###')[-1]
        progress_f = float(tmp_str.replace('%', ''))

        self.SetProgress(progress_f)

