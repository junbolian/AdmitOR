# IR: {"sets":{"T":[1,2,3,4],"K":[1,2,3,4],"C":"{(t,k) in T x K: t+k-1<=4}"},"params":{"demand_1":"month 1 demand","demand_2":"month 2 demand","demand_3":"month 3 demand","demand_4":"month 4 demand","price_1month":"monthly unit price for duration 1","price_2month":"monthly unit price for duration 2","price_3month":"monthly unit price for duration 3","price_4month":"monthly unit price for duration 4"},"variables":{"area[t,k]":{"index":"C","type":"NonNegativeReals"}},"constraints":["For each j in T: sum(area[t,k] for (t,k) in C if t<=j<=t+k-1)>=demand[j]"],"objective":{"sense":"minimize","expression":"sum(k*price[k]*area[t,k] for (t,k) in C)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
    }
    price = {
        1: params["price_1month"],
        2: params["price_2month"],
        3: params["price_3month"],
        4: params["price_4month"],
    }

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 4)
    model.durations = pyo.RangeSet(1, 4)
    model.contracts = pyo.Set(
        dimen=2,
        initialize=[
            (start, duration)
            for start in model.months
            for duration in model.durations
            if start + duration - 1 <= 4
        ],
    )

    model.demand = pyo.Param(model.months, initialize=demand)
    model.price = pyo.Param(model.durations, initialize=price)
    model.area = pyo.Var(model.contracts, domain=pyo.NonNegativeReals)

    def coverage_rule(instance, month):
        return sum(
            instance.area[start, duration]
            for start, duration in instance.contracts
            if start <= month <= start + duration - 1
        ) >= instance.demand[month]

    model.coverage = pyo.Constraint(model.months, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            duration * model.price[duration] * model.area[start, duration]
            for start, duration in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}