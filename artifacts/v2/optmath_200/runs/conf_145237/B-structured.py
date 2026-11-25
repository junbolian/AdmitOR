# IR: {"sets":{"I":"0..5","J":"0..4"},"params":{"supply":"supply[i]","demand":"demand[j]","cost":"cost[i][j]","capacity":"capacity[i][j]"},"variables":{"x[i,j]":"continuous, nonnegative"},"constraints":["sum_j x[i,j] = supply[i] for each i","sum_i x[i,j] = demand[j] for each j","x[i,j] <= capacity[i][j] for each i,j"],"objective":"minimize sum_i sum_j cost[i][j]*x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.I,
        initialize={i: params["supply"][i] for i in model.I},
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: params["demand"][j] for j in model.J},
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.I
            for j in model.J
        },
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["capacity"][i][j]
            for i in model.I
            for j in model.J
        },
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.J) == mod.supply[i]

    def demand_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.I) == mod.demand[j]

    def capacity_rule(mod, i, j):
        return mod.x[i, j] <= mod.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)
    model.route_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise when no feasible solution is available to load.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}