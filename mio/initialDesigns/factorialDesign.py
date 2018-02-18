# Copyright 2017 Prashant Singh, Andreas Hellander and Fredrik Wrede
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
Factorial Initial Design
"""

# Imports
from initialDesignBase import InitialDesignBase
import gpflowopt

# Class definition
class FactorialDesign(InitialDesignBase):
	"""
	Factorial design implemented through gpflowopt
	
	* InitialDesignBase.generate(n)
	"""
	
	def __init__(self, xmin, xmax):
		name = 'FactorialDesign'
		super(FactorialDesign,self).__init__(name, xmin, xmax)
		
	def generate(self, n):
		"""
		Sub-classable method for generating a factorial design of 'n' levels in the given 'domain'.
		The number of generated points is n^d.
		"""
		numVariables = len(self.xmin)
		gpfDomain = gpflowopt.domain.ContinuousParameter('x0', self.xmin[0], self.xmax[0])
		for i in range(1, numVariables):
			varName = 'x' + `i`
			gpfDomain = gpfDomain + gpflowopt.domain.ContinuousParameter(varName, self.xmin[i], self.xmax[i])
		
		design = gpflowopt.design.FactorialDesign(n, gpfDomain)
		return design.generate()
	