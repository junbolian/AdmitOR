import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    packets = [1, 2, 3, 4, 5, 6, 7]
    towers = ["T1", "T2", "T3"]

    capacity = {
        "T1": params["capacity_T1"],
        "T2": params["capacity_T2"],
        "T3": params["capacity_T3"],
    }
    usage = {
        "T1": {k: v for k, v in zip(packets, params["usage_T1"])},
        "T2": {k: v for k, v in zip(packets, params["usage_T2"])},
        "T3": {k: v for k, v in zip(packets, params["usage_T3"])},
    }
    cost = {
        "T1": {k: v for k, v in zip(packets, params["cost_T1"])},
        "T2": {k: v for k, v in zip(packets, params["cost_T2"])},
        "T3": {k: v for k, v in zip(packets, params["cost_T3"])},
    }

    model = pyo.ConcreteModel()
    model.packets = pyo.Set(initialize=packets)
    model.towers = pyo.Set(initialize=towers)

    model.assign = pyo.Var(model.packets, model.towers, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[t][p] * model.assign[p, t]
                 for p in model.packets for t in model.towers),
        sense=pyo.minimize,
    )

    model.assign_once = pyo.Constraint(
        model.packets,
        rule=lambda model, p: sum(model.assign[p, t] for t in model.towers) == 1,
    )

    model.capacity_limit = pyo.Constraint(
        model.towers,
        rule=lambda model, t: sum(usage[t][p] * model.assign[p, t]
                                  for p in model.packets) <= capacity[t],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}