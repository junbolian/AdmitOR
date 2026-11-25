# IR: {"sets":{"W":[0,1,2,3,4],"S":[0,1,2,3]},"params":{"supply":"supply[W]","demand":"demand[S]","cost":"cost[W,S]","capacity":"capacity[W,S]"},"variables":{"shipment[W,S]":"nonnegative continuous"},"constraints":["sum(shipment[w,s] for s in S) == supply[w] for w in W","sum(shipment[w,s] for w in W) == demand[s] for s in S","shipment[w,s] <= capacity[w,s] for (w,s) in W x S"],"objective":"minimize sum(cost[w,s]*shipment[w,s] for (w,s) in W x S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, 4)
    model.S = pyo.RangeSet(0, 3)

    model.supply = pyo.Param(
        model.W,
        initialize={w: params["supply"][w] for w in model.W},
    )
    model.demand = pyo.Param(
        model.S,
        initialize={s: params["demand"][s] for s in model.S},
    )
    model.cost = pyo.Param(
        model.W,
        model.S,
        initialize={
            (w, s): params["cost"][w][s]
            for w in model.W
            for s in model.S
        },
    )
    model.capacity = pyo.Param(
        model.W,
        model.S,
        initialize={
            (w, s): params["capacity"][w][s]
            for w in model.W
            for s in model.S
        },
    )

    model.shipment = pyo.Var(model.W, model.S, domain=pyo.NonNegativeReals)

    def supply_rule(instance, w):
        return (
            sum(instance.shipment[w, s] for s in instance.S)
            == instance.supply[w]
        )

    def demand_rule(instance, s):
        return (
            sum(instance.shipment[w, s] for w in instance.W)
            == instance.demand[s]
        )

    def capacity_rule(instance, w, s):
        return instance.shipment[w, s] <= instance.capacity[w, s]

    model.supply_balance = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.S, rule=demand_rule)
    model.route_capacity = pyo.Constraint(model.W, model.S, rule=capacity_rule)

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
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}