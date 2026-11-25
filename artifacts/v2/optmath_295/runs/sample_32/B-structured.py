# IR: {"sets":{"origins":[0,1,2,3,4],"destinations":[0,1,2,3,4]},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"flow[i,j]":"continuous, nonnegative"},"constraints":["sum_j flow[i,j] == supply[i] for each origin i","sum_i flow[i,j] == demand[j] for each destination j","flow[i,j] <= capacity[i,j] for each origin i and destination j"],"objective":"minimize sum_i sum_j cost[i,j] * flow[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: params["supply"][i] for i in model.origins},
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: params["demand"][j] for j in model.destinations},
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.origins
            for j in model.destinations
        },
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["capacity"][i][j]
            for i in model.origins
            for j in model.destinations
        },
    )

    model.flow = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(problem, i):
        return (
            sum(problem.flow[i, j] for j in problem.destinations)
            == problem.supply[i]
        )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=supply_rule,
    )

    def demand_rule(problem, j):
        return (
            sum(problem.flow[i, j] for i in problem.origins)
            == problem.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=demand_rule,
    )

    def capacity_rule(problem, i, j):
        return problem.flow[i, j] <= problem.capacity[i, j]

    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}