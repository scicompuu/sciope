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
Semi-supervised Label Propagation Surrogate Model
"""

# Imports
from sciope.models.model_base import ModelBase
from sklearn.semi_supervised import label_propagation
from scipy.optimize import basinhopping
from scipy.stats.distributions import entropy
import numpy as np



def get_label_entropies(label_distribution):
    return entropy(label_distribution.T)

def get_average_label_entropy(label_distribution):
    return get_label_entropies(label_distribution).sum()/label_distribution.shape[0]

# taken from documentation
class Bounds(object):
    def __init__(self, xmax, xmin):
        self.xmax = np.array(xmax)
        self.xmin = np.array(xmin)
    def __call__(self, **kwargs):
        x = kwargs["x_new"]
        tmax = bool(np.all(x <= self.xmax))
        tmin = bool(np.all(x >= self.xmin))
        return tmax and tmin

#taken from Stackoverflow: https://stackoverflow.com/questions/21670080/how-to-find-global-minimum-in-python-optimization-with-bounds
class RandomDisplacementBounds(object):
    """random displacement with bounds"""
    def __init__(self, xmax, xmin, stepsize=0.5):
        self.xmin = xmin
        self.xmax = xmax
        self.stepsize = stepsize

    def __call__(self, x):
        """take a random step but ensure the new position is within the bounds"""
        while True:
            # this could be done in a much more clever way, but it will work for example purposes
            xnew = x + np.random.uniform(-self.stepsize, self.stepsize, np.shape(x))
            if np.all(xnew < self.xmax) and np.all(xnew > self.xmin):
                break
        return xnew


# Class definition
class LPModel(ModelBase):
    """
    We use the sklearn Label Spreading implementation here.
    """

    def __init__(self, kernel='rbf', alpha=0.7, gamma=0.1, learning_rate=1.0):
        self.name = 'LPModel'
        self.kernel = kernel
        self.alpha = alpha
        self.gamma = gamma
        self.learning_rate = learning_rate

    # Tune parameters of the model
    def optimize(self, min_, max_, niter=10, stepsize = 0.1):
        step_routine = RandomDisplacementBounds(xmax = max_, xmin = min_, stepsize=stepsize)
        global_bounds = Bounds(xmax = max_, xmin = min_)
        start = np.random.uniform(min_, max_)

        #minimizer_bounds = [(low, high) for low, high in zip(min_, max_)]
        minimizer_bounds = [(min_, max_)]

        minimizer_kwargs = dict(method = "L-BFGS-B", bounds = minimizer_bounds)
        res = basinhopping(self.objective, start, minimizer_kwargs=minimizer_kwargs,
                   niter=niter, accept_test=global_bounds, take_step = step_routine, disp = True)
        return res.x

    def objective(self, x):
        model = label_propagation.LabelSpreading(kernel=self.kernel, alpha=self.alpha, 
                gamma=x)
        model.fit(self.x, self.y)
        label_prob = model.label_distributions_
        return get_average_label_entropy(label_prob) + self.learning_rate*x**2 

    # train the label propagation model given the data
    def train(self, inputs, targets, min_=0.01, max_=30, niter=10, stepsize=0.1):
        # Scale the training data
        self.x = inputs
        self.y = targets

        # Tune gamma in RBF using basinhopping 
        self.gamma = self.optimize(min_, max_, niter, stepsize)[0]

        # Propogate labels
        self.model = label_propagation.LabelSpreading(kernel=self.kernel, alpha=self.alpha, 
                    gamma=self.gamma)
        self.model.fit(self.x, self.y)

    # Predict
    def predict(self, xp):
        # predict
        yp = self.model.predict(xp)

        return yp
