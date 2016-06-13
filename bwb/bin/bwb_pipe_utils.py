#!/usr/bin/env python     
# -*- coding: utf-8 -*-     
# Copyright (C) 2016-2017 James Clark <james.clark@ligo.org>     
#     
# This program is free software; you can redistribute it and/or modify     
# it under the terms of the GNU General Public License as published by     
# the Free Software Foundation; either version 2 of the License, or     
# (at your option) any later version.     
# This program is distributed in the hope that it will be useful,     
# but WITHOUT ANY WARRANTY; without even the implied warranty of     
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     
# GNU General Public License for more details.     
#     
# You should have received a copy of the GNU General Public License along     
# with this program; if not, write to the Free Software Foundation, Inc.,     
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.    

# DAG Class definitions for bayeswave

from glue import pipeline
import itertools
import socket
import sys,os
import ast

#
# Main analysis
#

class bayeswaveJob(pipeline.CondorDAGJob,pipeline.AnalysisJob):

    def __init__(self, cp, cacheFiles, injfile=None, nrdata=None, dax=False):

        universe=cp.get('condor','universe')

        bayeswave = cp.get('bayeswave_paths','bayeswave')

        pipeline.CondorDAGJob.__init__(self,universe,bayeswave)
        pipeline.AnalysisJob.__init__(self,cp,dax=dax)

        if cp.has_option('condor', 'accounting_group'):
            self.add_condor_cmd('accounting_group', cp.get('condor', 'accounting_group'))   

        self.set_stdout_file('$(macrooutputDir)/bayeswave_$(cluster)-$(process)-$(node).out')
        self.set_stderr_file('$(macrooutputDir)/bayeswave_$(cluster)-$(process)-$(node).err')
        self.set_log_file('$(macrooutputDir)/bayeswave_$(cluster)-$(process)-$(node).log')

        #
        # Identify osg vs ldg site
        #
        # FIXME: currently only associates PACE (GaTech) as an OSG site
        hostname = socket.gethostname()
        #hostname = 'pace.gatech.edu'
        if 'pace.gatech.edu' in hostname:
            print >> sys.stdout, "Looks like you're on PACE; configuring file transfers"

            # --- Allow desired sites
            if cp.has_option('condor','desired-sites'):
                self.add_condor_cmd('+DESIRED_Sites',cp.get('condor','desired-sites'))

            # --- Perform file transfers
            self.add_condor_cmd('should_transfer_files', 'YES')
            self.add_condor_cmd('when_to_transfer_output', 'ON_EXIT_OR_EVICT')
            self.add_condor_cmd('transfer_output_files', '$(macrooutputDir)')

            # --- Files to include in transfer
            transferstring='datafind,$(macrooutputDir)'

            if cp.has_option('condor','transfer-files'):
                # allow specification of additional files to transfer
                transferstring+=',%s'%cp.get('condor','transfer-files')

            if cp.getboolean('condor','copy-frames'): transferstring+=',$(macroframes)'

            if injfile is not None:
                transferstring+=','+'SEOBNRv2ChirpTimeSS.dat,'+injfile
            if nrdata is not None: transferstring+=','+nrdata
            self.add_condor_cmd('transfer_input_files', transferstring)

            # --- Point to ROM data (which should have been copied
            if injfile is not None:
                self.add_condor_cmd("environment", "LAL_DATA_PATH=./")


        self.add_condor_cmd('getenv', 'True')

        # --- Required options
        ifo_list = ast.literal_eval(cp.get('input', 'ifo-list'))
        channel_list = ast.literal_eval(cp.get('datafind', 'channel-list'))

        # XXX: hack to repeat option for --ifo H1 --ifo L1 etc
        ifo_list_opt = ifo_list[0]
        for ifo in ifo_list[1:]: ifo_list_opt += ' --ifo {0}'.format(ifo)
        self.add_opt('ifo', ifo_list_opt)

        self.add_opt('srate', cp.get('input', 'srate'))
        self.add_opt('seglen', cp.get('input', 'seglen'))
        self.add_opt('PSDlength', cp.get('input', 'PSDlength'))
 
        flow = ast.literal_eval(cp.get('input','flow'))
        for ifo in ifo_list:
            self.add_opt('{ifo}-flow'.format(ifo=ifo), str(flow[ifo]))
            self.add_opt('{ifo}-cache'.format(ifo=ifo), cacheFiles[ifo])
            self.add_opt('{ifo}-channel'.format(ifo=ifo), channel_list[ifo])

        # --- Optional options


        # dataseed
        if cp.has_option('bayeswave_options', 'dataseed'):
            self.add_opt('dataseed', cp.get('bayeswave_options', 'dataseed'))

        # ----------------------------------------------------------------------------------
        # --- Run parameters   -------------------------------------------------------------
        # ----------------------------------------------------------------------------------

        # Niter
        if cp.has_option('bayeswave_options', 'Niter'):
            self.add_opt('Niter', cp.get('bayeswave_options', 'Niter'))

        # Nchain
        if cp.has_option('bayeswave_options', 'Nchain'):
            self.add_opt('Nchain', cp.get('bayeswave_options', 'Nchain'))
            
        # Ncycle
        if cp.has_option('bayeswave_options', 'Ncycle'):
            self.add_opt('Ncycle', cp.get('bayeswave_options', 'Ncycle'))

        # Nburnin
        if cp.has_option('bayeswave_options', 'Nburnin'):
            self.add_opt('Nburnin', cp.get('bayeswave_options', 'Nburnin'))

        # chainseed
        if cp.has_option('bayeswave_options', 'chainseed'):
            self.add_opt('chainseed', cp.get('bayeswave_options', 'chainseed'))

        # runName
        if cp.has_option('bayeswave_options', 'runName'):
            self.add_opt('runName', cp.get('bayeswave_options', 'runName'))

        # 0noise
        if cp.has_option('bayeswave_options', '0noise'):
            self.add_opt('0noise', cp.get('bayeswave_options', '0noise'))

        # zeroLogL
        if cp.has_option('bayeswave_options', 'zeroLogL'):
            self.add_opt('zeroLogL', cp.get('bayeswave_options', 'zeroLogL'))

        # restart
        if cp.has_option('bayeswave_options', 'restart'):
            self.add_opt('restart', cp.get('bayeswave_options', 'restart'))

        # gnuplot
        if cp.has_option('bayeswave_options', 'gnuplot'):
            self.add_opt('gnuplot', cp.get('bayeswave_options', 'gnuplot'))

        # verbose
        if cp.has_option('bayeswave_options', 'verbose'):
            self.add_opt('verbose', cp.get('bayeswave_options', 'verbose'))

        # window
        if cp.has_option('bayeswave_options', 'window'):
            self.add_opt('window', cp.get('bayeswave_options', 'window'))

        # self-checkpointing
        if cp.has_option('condor', 'checkpoint'):
            self.add_opt('checkpoint', cp.get('condor', 'checkpoint'))

        # version
        if cp.has_option('bayeswave_options', 'version'):
            self.add_opt('version', cp.get('bayeswave_options', 'version'))

        # help
        if cp.has_option('bayeswave_options', 'help'):
            self.add_opt('version', cp.get('bayeswave_options', 'help'))

        # ----------------------------------------------------------------------------------
        # --- Run parameters   -------------------------------------------------------------
        # ----------------------------------------------------------------------------------

        # fullOnly
        if cp.has_option('bayeswave_options', 'fullOnly'):
            self.add_opt('fullOnly', cp.get('bayeswave_options', 'fullOnly'))

        # noClean
        if cp.has_option('bayeswave_options', 'noClean'):
            self.add_opt('noClean', cp.get('bayeswave_options', 'noClean'))

        # noSignal
        if cp.has_option('bayeswave_options', 'noSignal'):
            self.add_opt('noSignal', cp.get('bayeswave_options', 'noSignal'))

        # cleanOnly
        if cp.has_option('bayeswave_options', 'cleanOnly'):
            self.add_opt('cleanOnly', cp.get('bayeswave_options', 'cleanOnly'))

        # noiseOnly
        if cp.has_option('bayeswave_options', 'noiseOnly'):
            self.add_opt('noiseOnly', cp.get('bayeswave_options', 'noiseOnly'))

        # signalOnly
        if cp.has_option('bayeswave_options', 'signalOnly'):
            self.add_opt('signalOnly', cp.get('bayeswave_options', 'signalOnly'))

        # glitchOnly
        if cp.has_option('bayeswave_options', 'glitchOnly'):
            self.add_opt('glitchOnly', cp.get('bayeswave_options', 'glitchOnly'))

        # noPSDfit
        if cp.has_option('bayeswave_options', 'noPSDfit'):
            self.add_opt('noPSDfit', cp.get('bayeswave_options', 'noPSDfit'))

        # bayesLine
        if cp.has_option('bayeswave_options', 'BayesLine'):
            self.add_opt('bayesLine', cp.get('bayeswave_options', 'BayesLine'))

        # stochastic
        if cp.has_option('bayeswave_options', 'stochastic'):
            self.add_opt('stochastic', cp.get('bayeswave_options', 'stochastic'))

        # ----------------------------------------------------------------------------------
        # --- Priors & Proposasl  ----------------------------------------------------------
        # ----------------------------------------------------------------------------------

        # Dimensions
        if cp.has_option('bayeswave_options', 'Dmin'):
            self.add_opt('Dmin', cp.get('bayeswave_options', 'Dmin'))
        if cp.has_option('bayeswave_options', 'Dmax'):
            self.add_opt('Dmax', cp.get('bayeswave_options', 'Dmax'))

        # fixD
        if cp.has_option('bayeswave_options', 'fixD'):
            self.add_opt('fixD', cp.get('bayeswave_options', 'fixD'))

        # Quality factor
        if cp.has_option('bayeswave_options', 'Qmin'):
            self.add_opt('Qmin', cp.get('bayeswave_options', 'Qmin'))
        if cp.has_option('bayeswave_options', 'Qmax'):
           self.add_opt('Qmax', cp.get('bayeswave_options', 'Qmax'))

        # clusterPrior
        if cp.has_option('bayeswave_options', 'clusterPrior'):
             self.add_opt('clusterPrior', cp.get('bayeswave_options',
                 'clusterPrior'))

        # clusterPath
        if cp.has_option('bayeswave_options', 'clusterPath'):
             self.add_opt('clusterPath', cp.get('bayeswave_options',
                 'clusterPath'))

        # clusterAlpha
        if cp.has_option('bayeswave_options', 'clusterAlpha'):
             self.add_opt('clusterAlpha', cp.get('bayeswave_options',
                 'clusterAlpha'))
        
        # clusterBeta
        if cp.has_option('bayeswave_options', 'clusterBeta'):
             self.add_opt('clusterBeta', cp.get('bayeswave_options',
                 'clusterBeta'))

        # clusterGamma
        if cp.has_option('bayeswave_options', 'clusterGamma'):
             self.add_opt('clusterGamma', cp.get('bayeswave_options',
                 'clusterGamma'))

        # backgroundPrior
        if cp.has_option('bayeswave_options', 'backgroundPrior'):
             self.add_opt('backgroundPrior', cp.get('bayeswave_options',
                 'backgroundPrior'))

        # orientationProposal
        if cp.has_option('bayeswave_options', 'orientationProposal'):
             self.add_opt('orientationProposal', cp.get('bayeswave_options',
                 'orientationProposal'))


        # uniformAmplitudePrior 
        if cp.has_option('bayeswave_options', 'uniformAmplitudePrior'):
             self.add_opt('uniformAmplitudePrior', cp.get('bayeswave_options',
                 'uniformAmplitudePrior'))

        # noSignalAmplitudePrior
        if cp.has_option('bayeswave_options', 'noSignalAmplitudePrior'):
             self.add_opt('noSignalAmplitudePrior', cp.get('bayeswave_options',
                 'noSignalAmplitudePrior'))

        # noAmplitudeProposal
        if cp.has_option('bayeswave_options', 'noAmplitudeProposal'):
             self.add_opt('noAmplitudeProposal', cp.get('bayeswave_options',
                 'noAmplitudeProposal'))

        # varyExtrinsicAmplitude
        if cp.has_option('bayeswave_options', 'varyExtrinsicAmplitude'):
             self.add_opt('varyExtrinsicAmplitude', cp.get('bayeswave_options',
                 'varyExtrinsicAmplitude'))

        # clusterProposal
        if cp.has_option('bayeswave_options', 'clusterProposal'):
             self.add_opt('clusterProposal', cp.get('bayeswave_options',
                 'clusterProposal'))

        # clusterWeight
        if cp.has_option('bayeswave_options', 'clusterWeight'):
             self.add_opt('', cp.get('bayeswave_options', 'clusterWeight'))

        # ampPriorPeak
        if cp.has_option('bayeswave_options', 'ampPriorPeak'):
             self.add_opt('', cp.get('bayeswave_options', 'ampPriorPeak'))

        # signalPriorPeak
        if cp.has_option('bayeswave_options', 'signalPriorPeak'):
             self.add_opt('', cp.get('bayeswave_options', 'signalPriorPeak'))

        # dimensionDecayRate
        if cp.has_option('bayeswave_options', 'dimensionDecayRate'):
             self.add_opt('', cp.get('bayeswave_options', 'dimensionDecayRate'))

        # fixIntrinsicParams
        if cp.has_option('bayeswave_options', 'fixIntrinsicParams'):
             self.add_opt('', cp.get('bayeswave_options', 'fixIntrinsicParams'))

        # fixExtrinsicParams
        if cp.has_option('bayeswave_options', 'fixExtrinsicParams'):
             self.add_opt('', cp.get('bayeswave_options', 'fixExtrinsicParams'))

        # ----------------------------------------------------------------------------------
        # --- Parallel Tempering parameters  -----------------------------------------------
        # ----------------------------------------------------------------------------------

        # tempMin
        if cp.has_option('bayeswave_options', 'tempMin'):
             self.add_opt('', cp.get('bayeswave_options', 'tempMin'))

        # noAdaptTemperature
        if cp.has_option('bayeswave_options', 'noAdaptTemperature'):
             self.add_opt('', cp.get('bayeswave_options', 'noAdaptTemperature'))
             k
        # tempSpacing
        if cp.has_option('bayeswave_options', 'tempSpacing'):
             self.add_opt('', cp.get('bayeswave_options', 'tempSpacing'))

        # noSplineEvidence
        if cp.has_option('bayeswave_options', 'noSplineEvidence'):
             self.add_opt('', cp.get('bayeswave_options', 'noSplineEvidence'))

        # ----------------------------------------------------------------------------------
        # --- LALInference Injection Options  ----------------------------------------------
        # ----------------------------------------------------------------------------------

        # Injection file
        if injfile is not None:
            injfile=os.path.join('..',injfile)
            self.add_opt('inj', injfile)

        # NR file
        if nrdata is not None:
            nrdata=os.path.join('..',nrdata)
            self.add_opt('inj-numreldata', nrdata)

        # ----------------------------------------------------------------------------------
        # --- Burst MDC injection ----------------------------------------------------------
        # ----------------------------------------------------------------------------------

        # mdc-cache
        if cp.has_option('injections', 'mdc-cache'):
            mdc_cache_list=str(['../datafind/MDC.cache' for ifo in
                ifo_list]).replace("'",'')
            mdc_cache_list=mdc_cache_list.replace(' ','')
            self.add_opt('MDC-cache', mdc_cache_list)

        # mdc-channels
        if cp.has_option('injections', 'mdc-channels'):
            mdc_channel_list=ast.literal_eval(cp.get('injections','mdc-channels'))
            mdc_channel_str=str(mdc_channel_list.values()).replace("'",'')
            mdc_channel_str=mdc_channel_str.replace(' ','')
            self.add_opt('MDC-channel', mdc_channel_str)

        # mdc-prefactor
        if cp.has_option('injections', 'mdc-prefactor'):
            self.add_opt('MDC-prefactor', cp.get('injections', 'mdc-prefactor'))

        # ----------------------------------------------------------------------------------
        # --- BayesWave internal injection options -----------------------------------------
        # ----------------------------------------------------------------------------------
        # BW-inject
        if cp.has_option('bayeswave_options', 'BW-inject'):
             self.add_opt('', cp.get('bayeswave_options', 'BW-inject'))

        # BW-injName
        if cp.has_option('bayeswave_options', 'BW-injName'):
             self.add_opt('', cp.get('bayeswave_options', 'BW-injName'))

        # BW-path
        if cp.has_option('bayeswave_options', 'BW-path'):
             self.add_opt('', cp.get('bayeswave_options', 'BW-path'))

        # BW-event
        if cp.has_option('bayeswave_options', 'BW-event'):
             self.add_opt('', cp.get('bayeswave_options', 'BW-event'))

        # XXX: where is this?
        # NC
        if cp.has_option('bayeswave_options','NC'):
            self.add_opt('NC', cp.get('bayeswave_options', 'NC'))
        # NCmin
        if cp.has_option('bayeswave_options','NCmin'):
            self.add_opt('NCmin', cp.get('bayeswave_options', 'NCmin'))
        # NCmax
        if cp.has_option('bayeswave_options','NCmax'):
            self.add_opt('NCmax', cp.get('bayeswave_options', 'NCmax'))



        self.set_sub_file('bayeswave.sub')

class bayeswaveNode(pipeline.CondorDAGNode, pipeline.AnalysisNode):

    def __init__(self, bayeswave_job):

        pipeline.CondorDAGNode.__init__(self,bayeswave_job)
        pipeline.AnalysisNode.__init__(self)

    def set_trigtime(self, trigtime):
        self.add_var_opt('trigtime', trigtime)
        self.__trigtime = trigtime

    def set_PSDstart(self, PSDstart):
        self.add_var_opt('PSDstart', PSDstart)
        self.__PSDstart = PSDstart

    def set_outputDir(self, outputDir):
        self.add_var_opt('outputDir', outputDir)
        self.__outputDir = outputDir

    def set_injevent(self, event):
        self.add_var_opt('event', event)
        self.__event = event

    def set_dataseed(self, dataseed):
        self.add_var_opt('dataseed', dataseed)
        self.__dataseed = dataseed

    def add_frame_transfer(self, framedict):
        """
        Add a list of frames to transfer
        """
        self.__frames=""
        for ifo in framedict.keys():
            for frame in framedict[ifo]:
                self.__frames += frame + ','
        self.__frames.strip(',')
        self.add_var_opt('frames', self.__frames)
  
    def set_L1_timeslide(self, L1_timeslide):
        self.add_var_opt('L1-timeslide', L1_timeslide)
        self.__L1_timeslide = L1_timeslide

#
# Post-processing
#

class bayeswave_postJob(pipeline.CondorDAGJob,pipeline.AnalysisJob):

    def __init__(self, cp, cacheFiles, injfile=None, nrdata=None, dax=False):

        universe=cp.get('condor','universe')

        bayeswave_post = cp.get('bayeswave_paths','bayeswave_post')

        pipeline.CondorDAGJob.__init__(self,universe,bayeswave_post)
        pipeline.AnalysisJob.__init__(self,cp,dax=dax)

        if cp.has_option('condor', 'accounting_group'):
            self.add_condor_cmd('accounting_group', cp.get('condor', 'accounting_group'))   

        self.set_stdout_file('$(macrooutputDir)/bayeswave_post_$(cluster)-$(process)-$(node).out')
        self.set_stderr_file('$(macrooutputDir)/bayeswave_post_$(cluster)-$(process)-$(node).err')
        self.set_log_file('$(macrooutputDir)/bayeswave_post_$(cluster)-$(process)-$(node).log')

        # Request 4GB of RAM for pp jobs
        self.add_condor_cmd('request_memory', '4000')

        #
        # Identify osg vs ldg site
        #
        # FIXME: currently only associates PACE (GaTech) as an OSG site
        hostname = socket.gethostname()
        if 'pace.gatech.edu' in hostname:
            print >> sys.stdout, "Looks like you're on PACE; configuring file transfers"

            # --- Allow desired sites
            +DESIRED_Sites = "GATech"
            if cp.has_option('condor','desired-sites'):
                self.add_condor_cmd('+DESIRED_Sites',cp.get('condor','desired-sites'))

            # --- Perform file transfers
            self.add_condor_cmd('should_transfer_files', 'YES')
            self.add_condor_cmd('when_to_transfer_output', 'ON_EXIT_OR_EVICT')
            self.add_condor_cmd('transfer_output_files', '$(macrooutputDir)')

            # --- Files to include in transfer
            # FIXME: PostProc doesn't currently need frame transfer
            transferstring='datafind,$(macrooutputDir)'

            if cp.has_option('condor','transfer-files'):
                # allow specification of additional files to transfer
                transferstring+=',%s'%cp.get('condor','transfer-files')

            if injfile is not None:
                transferstring+=','+'SEOBNRv2ChirpTimeSS.dat,'+injfile
            if nrdata is not None: transferstring+=','+nrdata
            self.add_condor_cmd('transfer_input_files', transferstring)

            # --- Point to ROM data (which should have been copied
            if injfile is not None:
                self.add_condor_cmd("environment", 'LAL_DATA_PATH="./"')

        self.add_condor_cmd('getenv', 'True')

        # --- Required options
        ifo_list = ast.literal_eval(cp.get('input', 'ifo-list'))
        channel_list = ast.literal_eval(cp.get('datafind', 'channel-list'))

        # XXX: hack to repeat option
        ifo_list_opt = ifo_list[0]
        for ifo in ifo_list[1:]:
            ifo_list_opt += ' --ifo {0}'.format(ifo)
        self.add_opt('ifo', ifo_list_opt)

        self.add_opt('srate', cp.get('input', 'srate'))
        self.add_opt('seglen', cp.get('input', 'seglen'))
        self.add_opt('PSDlength', cp.get('input', 'PSDlength'))
 
        flow = ast.literal_eval(cp.get('input','flow'))
        for ifo in ifo_list:
            self.add_opt('{ifo}-flow'.format(ifo=ifo), str(flow[ifo]))

            # XXX: Postproc currently expects LALSimAdLIGO
            self.add_opt('{ifo}-cache'.format(ifo=ifo), "LALSimAdLIGO")
            self.add_opt('{ifo}-channel'.format(ifo=ifo), "LALSimAdLIGO")


        # --- Optional options
        # bayesLine
        if cp.has_option('bayeswave_post_options', 'BayesLine'):
            self.add_opt('bayesLine', cp.get('bayeswave_post_options', 'BayesLine'))

        # 0noise
        if cp.has_option('bayeswave_post_options', '0noise'):
            self.add_opt('0noise', cp.get('bayeswave_post_options', '0noise'))

        #
        # Injection file
        #
        if injfile is not None:
            # XXX: note that bayeswave works within the outputDir, so point to
            # injection
            injfile=os.path.join('..',injfile)
            self.add_opt('inj', injfile)

        if nrdata is not None:
            nrdata=os.path.join('..',nrdata)
            self.add_opt('inj-numreldata', nrdata)

        #
        # MDC Setup
        #
        if cp.has_option('injections', 'mdc-cache'):
            mdc_cache_list=str(['../datafind/MDC.cache' for ifo in
                ifo_list]).replace("'",'')
            mdc_cache_list=mdc_cache_list.replace(' ','')
            self.add_opt('MDC-cache', mdc_cache_list)

        if cp.has_option('injections', 'mdc-channels'):
            #mdc_channel_list=ast.literal_eval(cp.get('injections','mdc-channels'))
            mdc_channel_list=ast.literal_eval(cp.get('injections','mdc-channels'))
            mdc_channel_str=str(mdc_channel_list.values()).replace("'",'')
            mdc_channel_str=mdc_channel_str.replace(' ','')
            self.add_opt('MDC-channel', mdc_channel_str)

        if cp.has_option('injections', 'mdc-prefactor'):
            self.add_opt('MDC-prefactor', cp.get('injections', 'mdc-prefactor'))


        self.set_sub_file('bayeswave_post.sub')


class bayeswave_postNode(pipeline.CondorDAGNode, pipeline.AnalysisNode):

    def __init__(self, bayeswave_post_job):

        pipeline.CondorDAGNode.__init__(self, bayeswave_post_job)
        pipeline.AnalysisNode.__init__(self)

    def set_trigtime(self, trigtime):
        self.add_var_opt('trigtime', trigtime)
        self.__trigtime = trigtime

    def set_PSDstart(self, PSDstart):
        self.add_var_opt('PSDstart', PSDstart)
        self.__PSDstart = PSDstart

    def set_outputDir(self, outputDir):
        self.add_var_opt('outputDir', outputDir)
        self.__outputDir = outputDir

    def set_injevent(self, event):
        self.add_var_opt('event', event)
        self.__event = event

    def set_dataseed(self, dataseed):
        self.add_var_opt('dataseed', dataseed)
        self.__dataseed = dataseed

    def set_L1_timeslide(self, L1_timeslide):
        self.add_var_opt('L1-timeslide', L1_timeslide)
        self.__L1_timeslide = L1_timeslide


#
# skymap job
#

class megaskyJob(pipeline.CondorDAGJob,pipeline.AnalysisJob):

    def __init__(self, cp, dax=False):

        # XXX consider local universe?
        universe='vanilla'

        # Point this to the src dir
        megasky = cp.get('bayeswave_paths','megasky')
        pipeline.CondorDAGJob.__init__(self,universe,megasky)
        pipeline.AnalysisJob.__init__(self,cp,dax=dax)

        if cp.has_option('condor', 'accounting_group'):
            self.add_condor_cmd('accounting_group', cp.get('condor', 'accounting_group'))   

        self.set_stdout_file('megasky_$(cluster)-$(process)-$(node).out')
        self.set_stderr_file('megasky_$(cluster)-$(process)-$(node).err')
        self.set_log_file('megasky_$(cluster)-$(process)-$(node).log')
        self.set_sub_file('megasky.sub')

        if 'pace.gatech.edu' in hostname:
            print >> sys.stdout, "Looks like you're on PACE; configuring file transfers"

            # --- Allow desired sites
            +DESIRED_Sites = "GATech"
            if cp.has_option('condor','desired-sites'):
                self.add_condor_cmd('+DESIRED_Sites',cp.get('condor','desired-sites'))


class megaskyNode(pipeline.CondorDAGNode, pipeline.AnalysisNode):

    def __init__(self, megasky_job, rundir):

        pipeline.CondorDAGNode.__init__(self, megasky_job)
        pipeline.AnalysisNode.__init__(self)
        # Set job initialdir, so python codes know where to expect input files
        self.add_var_condor_cmd('initialdir', rundir)   
        self.__rundir = rundir

#
# megaplot job
#

class megaplotJob(pipeline.CondorDAGJob,pipeline.AnalysisJob):

    def __init__(self, cp, dax=False):

        universe='vanilla'

        # Point this to the src dir
        megaplot = cp.get('bayeswave_paths','megaplot')
        pipeline.CondorDAGJob.__init__(self,universe, megaplot)
        pipeline.AnalysisJob.__init__(self,cp,dax=dax)

        if 'pace.gatech.edu' in hostname:
            print >> sys.stdout, "Looks like you're on PACE; configuring file transfers"

            # --- Allow desired sites
            +DESIRED_Sites = "GATech"
            if cp.has_option('condor','desired-sites'):
                self.add_condor_cmd('+DESIRED_Sites',cp.get('condor','desired-sites'))

        if cp.has_option('condor', 'accounting_group'):
            self.add_condor_cmd('accounting_group', cp.get('condor', 'accounting_group'))   

        self.set_stdout_file('megaplot_$(cluster)-$(process)-$(node).out')
        self.set_stderr_file('megaplot_$(cluster)-$(process)-$(node).err')
        self.set_log_file('megaplot_$(cluster)-$(process)-$(node).log')
        self.set_sub_file('megaplot.sub')


class megaplotNode(pipeline.CondorDAGNode, pipeline.AnalysisNode):

    def __init__(self, megaplot_job, rundir):

        pipeline.CondorDAGNode.__init__(self, megaplot_job)
        pipeline.AnalysisNode.__init__(self)
        # Set job initialdir, so python codes know where to expect input files
        self.add_var_condor_cmd('initialdir', rundir)   
        self.__rundir = rundir


