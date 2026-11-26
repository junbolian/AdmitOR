# IR: {"sets":{"T":[1,2,3,4],"K":[1,2,3,4],"A":"{(s,k) in T x K : s+k-1 <= 4}"},"params":{"demand":"required area indexed by T","cost_1":"total fee per area for duration 1","cost_2":"total fee per area for duration 2","cost_3":"total fee per area for duration 3","cost_4":"total fee per area for duration 4"},"variables":{"area[s,k]":"nonnegative continuous, (s,k) in A"},"constraints":["coverage[t]: sum(area[s,k] for (s,k) in A if s <= t < s+k) >= demand[t], for t in T"],"objective":"minimize sum(cost_k * area[s,k] for (s,k) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using demand as a four-item sequence or a month-keyed mapping."""
    demand_input = params["demand"]
    rental_costs = {
        1: params["cost_1"],
        2: params["cost_2"],
        3: params["cost_3"],
        4: params["cost_4"],
    }

    months = range(1, 5)
    if isinstance(demand_input, Mapping):
        demand_values = {month: demand_input[month] for month in months}
    else:
        demand_values = {
            month: demand_input[month - 1] for month in months
        }

    model = pyo.ConcreteModel()
    model.months = pyo.Set(initialize=months, ordered=True)
    model.durations = pyo.Set(initialize=range(1, 5), ordered=True)
    model.contracts = pyo.Set(
        dimen=2,
        initialize=[
            (start, duration)
            for start in months
            for duration in range(1, 5)
            if start + duration - 1 <= 4
        ],
    )

    model.required_area = pyo.Param(
        model.months, initialize=demand_values
    )
    model.rental_cost = pyo.Param(
        model.durations, initialize=rental_costs
    )
    model.area = pyo.Var(
        model.contracts, domain=pyo.NonNegativeReals
    )

    def coverage_rule(instance, month):
        return sum(
            instance.area[start, duration]
            for start, duration in instance.contracts
            if start <= month < start + duration
        ) >= instance.required_area[month]

    model.coverage = pyo.Constraint(
        model.months, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.rental_cost[duration] * model.area[start, duration]
            for start, duration in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when its default solution loading finds no
        # feasible solution. Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}