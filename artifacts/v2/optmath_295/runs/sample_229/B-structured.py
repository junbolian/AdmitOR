# IR: {"sets":{"W":[0,1,2,3],"S":[0,1,2,3,4]},"params":{"supply":"params['supply'][w], nonnegative","demand":"params['demand'][s], nonnegative","cost":"params['cost'][w][s], real","capacity":"params['capacity'][w][s], nonnegative"},"variables":{"shipment[w,s]":"continuous, nonnegative"},"constraints":["sum(shipment[w,s] for s in S) == supply[w] for each w in W","sum(shipment[w,s] for w in W) == demand[s] for each s in S","shipment[w,s] <= capacity[w,s] for each (w,s) in W x S"],"objective":"minimize sum(cost[w,s] * shipment[w,s] for (w,s) in W x S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=range(4), ordered=True)
    model.S = pyo.Set(initialize=range(5), ordered=True)

    model.supply = pyo.Param(
        model.W,
        initialize={w: params["supply"][w] for w in model.W},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.S,
        initialize={s: params["demand"][s] for s in model.S},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.W,
        model.S,
        initialize={
            (w, s): params["cost"][w][s]
            for w in model.W
            for s in model.S
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.W,
        model.S,
        initialize={
            (w, s): params["capacity"][w][s]
            for w in model.W
            for s in model.S
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.W, model.S, domain=pyo.NonNegativeReals
    )

    def supply_rule(mod, w):
        return sum(mod.shipment[w, s] for s in mod.S) == mod.supply[w]

    def demand_rule(mod, s):
        return sum(mod.shipment[w, s] for w in mod.W) == mod.demand[s]

    def capacity_rule(mod, w, s):
        return mod.shipment[w, s] <= mod.capacity[w, s]

    model.supply_balance = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.S, rule=demand_rule)
    model.lane_capacity = pyo.Constraint(
        model.W, model.S, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[w, s] * model.shipment[w, s]
            for w in model.W
            for s in model.S
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}