# IR: {"sets":{"DC":"0..6","STORE":"0..7"},"params":{"fixed_cost_dc":"real[DC]","shipping_cost":"real[DC,STORE]","store_demand":"nonnegative_real[STORE]","dc_capacity":"nonnegative_real[DC]"},"variables":{"open_dc":"binary[DC]","ship":"nonnegative_real[DC,STORE]"},"constraints":["For each store j: sum_i ship[i,j] = store_demand[j]","For each DC i: sum_j ship[i,j] <= dc_capacity[i] * open_dc[i]"],"objective":"minimize sum_i fixed_cost_dc[i] * open_dc[i] + sum_i,j shipping_cost[i,j] * ship[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 6)
    model.STORE = pyo.RangeSet(0, 7)

    model.fixed_cost_dc = pyo.Param(
        model.DC,
        initialize={i: params["fixed_cost_dc"][i] for i in model.DC},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): params["shipping_cost"][i][j]
            for i in model.DC
            for j in model.STORE
        },
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.STORE,
        initialize={j: params["store_demand"][j] for j in model.STORE},
        within=pyo.NonNegativeReals,
    )
    model.dc_capacity = pyo.Param(
        model.DC,
        initialize={i: params["dc_capacity"][i] for i in model.DC},
        within=pyo.NonNegativeReals,
    )

    model.open_dc = pyo.Var(model.DC, domain=pyo.Binary)
    model.ship = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(problem, j):
        return (
            sum(problem.ship[i, j] for i in problem.DC)
            == problem.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(problem, i):
        return (
            sum(problem.ship[i, j] for j in problem.STORE)
            <= problem.dc_capacity[i] * problem.open_dc[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost_dc[i] * model.open_dc[i]
                for i in model.DC
            )
            + sum(
                model.shipping_cost[i, j] * model.ship[i, j]
                for i in model.DC
                for j in model.STORE
            )
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