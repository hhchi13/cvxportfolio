# Copyright 2016 Enzo Busseti, Stephen Boyd, Steven Diamond, BlackRock Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module contains classes to make forecasts such as historical means
and covariances and are used internally by cvxportfolio objects. In addition,
forecast classes have the ability to cache results online so that if multiple
classes need access to the estimated value (as is the case in MultiPeriodOptimization
policies) the expensive evaluation is only done once. 
"""

import numpy as np

from .estimator import Estimator


class BaseForecast(Estimator):
    """Base class for forecasters."""
    
    # def pre_evaluation(self, universe, backtest_times):
    #     self.universe = universe
    #     self.backtest_times = backtest_times


class HistoricalMeanReturn(BaseForecast):
    """Historical mean returns."""
    
    def __init__(self, lastforcash):
        self.lastforcash = lastforcash
    
    def values_in_time(self, t, past_returns, **kwargs):
        super().values_in_time(t=t, past_returns=past_returns, **kwargs)
        self.current_value = past_returns.mean().values
        if self.lastforcash:
            self.current_value[-1] = past_returns.iloc[-1, -1]
        return self.current_value
        
    @classmethod # we make it a classmethod so that also covariances can use it
    def update_full_mean(cls, past_returns, last_estimation, last_counts, last_time):

        if last_time is None: # full estimation
            estimation = past_returns.sum()
            counts = past_returns.count()
        else:
            assert last_time == past_returns.index[-2]
            estimation = last_estimation * last_counts + past_returns.iloc[-1].fillna(0.)
            counts = last_counts + past_returns.iloc[-1:].count()

        return estimation/counts, counts, past_returns.index[-1]
        
        
class HistoricalMeanError(BaseForecast):
    """Historical standard deviations of the mean."""

    def __init__(self, zeroforcash):
        self.zeroforcash = zeroforcash
    
    def values_in_time(self, t, past_returns, **kwargs):
        super().values_in_time(t=t, past_returns=past_returns, **kwargs)
        self.current_value  = (past_returns.std() / np.sqrt(past_returns.count())).values
        if self.zeroforcash:
            self.current_value[-1] = 0.
        return self.current_value  
        
        
class HistoricalVariance(BaseForecast):
    """Historical variances."""

    def __init__(self, zeroforcash, addmean):
        self.zeroforcash = zeroforcash
        self.addmean = addmean
    
    def values_in_time(self, t, past_returns, **kwargs):
        super().values_in_time(t=t, past_returns=past_returns, **kwargs)
        
        tmp  = past_returns.var(ddof=0) 
        
        if self.addmean:
            tmp += past_returns.mean()**2
        
        tmp = tmp.values
        
        if self.zeroforcash:
            tmp[-1] = 0.
            
        self.current_value = tmp
        return self.current_value  
        
          
class HistoricalFactorizedCovariance(BaseForecast):
    """Historical covariance matrix, sqrt factorized."""
    
    def __init__(self, addmean, zeroforcash):
        self.addmean = addmean
        self.zeroforcash = zeroforcash
    
    @classmethod
    def get_count_matrix(cls, past_returns):
        """We obtain the matrix of non-null joint counts."""
        tmp = ~past_returns.isnull()
        return len(past_returns) * (tmp.cov(ddof=0) + np.outer(tmp.mean(), tmp.mean()))

    @classmethod # we make it a classmethod so that also covariances can use it
    def update_full_covariance(cls, past_returns, last_estimation, last_counts, last_time):

        if last_time is None: # full estimation
            estimation = past_returns.iloc[:,:-1].cov()
            counts = self.get_count_matrix(past_returns)
        else:
            assert last_time == past_returns.index[-2]

            estimation = last_estimation * last_counts + past_returns.iloc[-1:].fillna(0.)
            counts = last_counts + past_returns.iloc[-1:].count()

        return estimation, counts, past_returns.index[-1]
    
    
    def values_in_time(self, t, past_returns, **kwargs):
        super().values_in_time(t=t, past_returns=past_returns, **kwargs)
    
        Sigma = past_returns.cov(ddof=0)
        if self.addmean:
            mean = past_returns.mean()
            Sigma += np.outer(mean, mean)
        if self.zeroforcash:
            Sigma.iloc[:, -1] = 0
            Sigma.iloc[-1, :] = 0

        eigval, eigvec = np.linalg.eigh(Sigma)

        eigval = np.maximum(eigval, 0.)
    
        self.current_value = eigvec @ np.diag(np.sqrt(eigval))
        
        return self.current_value