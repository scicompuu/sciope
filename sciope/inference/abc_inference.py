# Copyright 2017 Prashant Singh, Fredrik Wrede and Andreas Hellander
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Approximate Bayesian Computation
"""

# Imports
from sciope.inference.inference_base import InferenceBase
from sciope.utilities.distancefunctions import euclidean as euc
from sciope.utilities.summarystats import burstiness as bs
from sciope.utilities.housekeeping import sciope_logger as ml
from sciope.utilities.housekeeping import sciope_profiler
from sciope.data.dataset import DataSet
import multiprocessing as mp
import numpy as np

# The following variable stores n normalized distance values after n summary statistics have been calculated
normalized_distances = None

# Set up the logger
logger = ml.SciopeLogger().get_logger()


# Class definition: multiprocessing ABC process
class ABCProcess(mp.Process):
    """
    The process class used to distribute the sampling process
    """

    def run(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


# Class definition: ABC rejection sampling
class ABC(InferenceBase):
    """
    Approximate Bayesian Computation Rejection Sampler

    * InferenceBase.infer()
    """

    def __init__(self, data, sim, prior_function, epsilon=0.1, parallel_mode=True, summaries_function=bs.Burstiness(),
                 distance_function=euc.EuclideanDistance()):
        self.name = 'ABC'
        self.epsilon = epsilon
        self.summaries_function = summaries_function
        self.prior_function = prior_function
        self.distance_function = distance_function
        self.parallel_mode = parallel_mode
        self.historical_distances = []
        super(ABC, self).__init__(self.name, data, sim)
        logger.info("Approximate Bayesian Computation initialized")

    def scale_distance(self, dist):
        """
        Performs scaling in [0,1] of a given distance vector/value with respect to historical distances
        :param dist: a distance value or vector
        :return: scaled distance value or vector
        """
        global normalized_distances
        self.historical_distances.append(dist.ravel())
        all_distances = np.array(self.historical_distances)
        divisor = np.asarray(all_distances.max(axis=0))
        normalized_distances = all_distances
        for j in range(0, len(divisor), 1):
            if divisor[j] > 0:
                normalized_distances[:, j] = normalized_distances[:, j] / divisor[j]

        return normalized_distances[-1, :]

    @sciope_profiler.profile
    def rejection_sampling(self, num_samples):
        """
        Perform ABC inference according to initialized configuration.
        :return:
        posterior: The posterior distribution (samples)
        distances: Accepted distance values
        accepted_count: Number of accepted samples
        trial_count: The number of total trials performed in order to converge
        """
        accepted_count = 0
        trial_count = 0
        accepted_samples = []
        distances = []
        fixed_dataset = DataSet('Fixed Data')
        sim_dataset = DataSet('Simulated Data')
        fixed_dataset.add_points(targets=self.data, summary_stats=self.summaries_function.compute(self.data))

        while accepted_count < num_samples:
            # Rejection sampling
            # Draw from the prior
            trial_param = self.prior_function.draw()

            # Perform the trial
            sim_result = self.sim(trial_param)

            # Get the statistic(s)
            sim_stats = self.summaries_function.compute(sim_result)

            # Set/Update simulated dataset
            sim_dataset.add_points(targets=sim_result, summary_stats=sim_stats)

            # Calculate the distance between the dataset and the simulated result
            sim_dist = self.distance_function.compute(fixed_dataset.s, sim_stats)

            # Normalize distances between [0,1]
            sim_dist_scaled = self.scale_distance(sim_dist)

            # Take the norm to combine the distances
            combined_distance = np.linalg.norm(sim_dist_scaled)
            logger.debug("Rejection Sampling: trial parameter = [{0}], distance = [{1}]".format(trial_param,
                                                                                                combined_distance))

            # Accept/Reject
            if combined_distance <= self.epsilon:
                accepted_samples.append(trial_param)
                distances.append(sim_dist)
                accepted_count += 1
                logger.info("Rejection Sampling: accepted a new sample, total accepted samples = {0}".
                            format(len(accepted_samples)))

            trial_count += 1

        self.results = {'accepted_samples': accepted_samples, 'distances': distances, 'accepted_count': accepted_count,
                   'trial_count': trial_count, 'inferred_parameters': np.mean(accepted_samples, axis=0)}
        return self.results

    def perform_abc(self, num_samples, output):
        """
        Wrapper function for rejection sampling.
        :param num_samples: The desired number of accepted samples
        :param output: The multiprocessing output queue
        :return:
        """
        output.put(self.rejection_sampling(num_samples))

    def process_queue_outputs(self, x):
        """
        Post-processing of rejection sampling results for parallel ABC
        :return:
        """
        accepted_samples = []
        distances = []
        for p in x:
            accepted_samples.append(p['accepted_samples'])
            distances.append(p['distances'])

        flat_posteriors_list = [item for sublist in accepted_samples for item in sublist]
        flat_distances_list = [item for sublist in distances for item in sublist]

        accepted_count = sum([p['accepted_count'] for p in x])
        trial_count = sum([p['trial_count'] for p in x])

        self.results = {'accepted_samples': flat_posteriors_list, 'distances': flat_distances_list,
                        'accepted_count': accepted_count, 'trial_count': trial_count,
                        'inferred_parameters': np.mean(flat_posteriors_list, axis=0)}
        logger.info("\n\nInferred parameters: {0}".format(self.results['inferred_parameters']))
        logger.info("Trial count: {0}".format(self.results['trial_count']))
        return self.results

    def infer(self, num_samples):
        """
        Perform serial or parallel ABC.
        :param num_samples: The desired number of accepted samples
        :return:
        posterior: The posterior distribution (samples)
        distances: Accepted distance values
        accepted_count: Number of accepted samples
        trial_count: The number of total trials performed in order to converge
        """
        if not self.parallel_mode:
            # Serial ABC
            return self.rejection_sampling(num_samples)
        else:
            # Parallel ABC
            proc_count = mp.cpu_count()
            chunks_count = np.ceil(num_samples / float(proc_count))
            logger.info("Parallel ABC: Running {0} samples on {1} processors...".format(chunks_count, proc_count))
            output = mp.Queue()
            processes = [ABCProcess(target=self.perform_abc, args=(chunks_count, output))
                         for i in range(proc_count)]
            for p in processes:
                p.start()

            for p in processes:
                p.join()

            process_results = [output.get() for p in processes]
            return self.process_queue_outputs(process_results)
