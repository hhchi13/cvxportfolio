# Copyright 2023- The Cvxportfolio Contributors
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


import cvxpy as cvx
import numpy as np
import pandas as pd
import pytest
import numpy as np

from cvxportfolio.returns import *


def test_returns_forecast(returns):

    N = returns.shape[1]
    alpha_model = ReturnsForecast(returns)
    alpha_model.pre_evaluation(None, None, returns.index[0], None)
    w_plus = cvx.Variable(N)
    cvxpy_expression = alpha_model.compile_to_cvxpy(w_plus, None, None)
    alpha_model.values_in_time(returns.index[123], None, None, None, None)
    w_plus.value = np.random.randn(N)
    assert np.isclose(cvxpy_expression.value, w_plus.value @ returns.iloc[123])


def test_rolling_mean_returns_forecast(returns):

    N = returns.shape[1]
    alpha_model = ReturnsForecast(rolling=50)
    alpha_model.pre_evaluation(returns, None, returns.index[50], None)
    w_plus = cvx.Variable(N)

    t = returns.index[123]
    cvxpy_expression = alpha_model.compile_to_cvxpy(w_plus, None, None)
    alpha_model.values_in_time(t, None, None, None, None)
    w_plus.value = np.random.randn(N)
    myforecast = returns.loc[returns.index < t].iloc[-50:].mean()
    myforecast.iloc[-1] = returns.iloc[122, -1]

    assert np.isclose(cvxpy_expression.value, w_plus.value @ myforecast)
    
    
def test_full_returns_forecast(returns):

    N = returns.shape[1]
    alpha_model = ReturnsForecast()
    alpha_model.pre_evaluation(returns, None, returns.index[50], None)
    w_plus = cvx.Variable(N)

    t = returns.index[123]
    cvxpy_expression = alpha_model.compile_to_cvxpy(w_plus, None, None)
    alpha_model.values_in_time(t, None, None, returns.loc[returns.index<t], None)
    w_plus.value = np.random.randn(N)
    myforecast = returns.loc[returns.index < t].mean()
    myforecast.iloc[-1] = returns.iloc[122, -1]

    assert np.isclose(cvxpy_expression.value, w_plus.value @ myforecast)


def test_exponential_mean_returns_forecast(returns):

    N = returns.shape[1]
    alpha_model = ReturnsForecast(halflife=25)
    alpha_model.pre_evaluation(returns, None, returns.index[50], None)
    w_plus = cvx.Variable(N)

    t = returns.index[123]
    cvxpy_expression = alpha_model.compile_to_cvxpy(w_plus, None, None)
    alpha_model.values_in_time(t, None, None, None, None)
    w_plus.value = np.random.randn(N)
    myforecast = returns.loc[returns.index < t].ewm(
        halflife=25).mean().iloc[-1]
    myforecast.iloc[-1] = returns.iloc[122, -1]

    assert np.isclose(cvxpy_expression.value, w_plus.value @ myforecast)


def test_returns_forecast_error(returns):

    delta = returns.std() / np.sqrt(len(returns))
    N = returns.shape[1]

    error_risk = ReturnsForecastErrorRisk(delta)
    error_risk.pre_evaluation(returns, None, returns.index[0], None)
    w_plus = cvx.Variable(N)
    cvxpy_expression = error_risk.compile_to_cvxpy(w_plus, None, None)
    error_risk.values_in_time(0, None, None, None, None)

    w_plus.value = np.random.randn(N)
    assert np.isclose(cvxpy_expression.value, np.abs(w_plus.value) @ delta)


def test_rolwin_returns_forecast_error(returns):

    N = returns.shape[1]
    error_risk = RollingWindowReturnsForecastErrorRisk(lookback_period=20)
    error_risk.pre_evaluation(returns, None, returns.index[50], None)
    w_plus = cvx.Variable(N)

    t = returns.index[123]
    cvxpy_expression = error_risk.compile_to_cvxpy(w_plus, None, None)
    error_risk.values_in_time(t, None, None, None, None)
    w_plus.value = np.random.randn(N)
    delta = returns.loc[returns.index < t].iloc[-20:].std() / np.sqrt(20)
    delta.iloc[-1] = 0.

    assert np.isclose(cvxpy_expression.value, np.abs(w_plus.value) @ delta)
