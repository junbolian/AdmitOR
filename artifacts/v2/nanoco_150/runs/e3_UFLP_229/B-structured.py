# IR: {"sets":{"I":"0..18","J":"0..4"},"params":{"fixed_cost_hub_0":"real","fixed_cost_hub_1":"real","fixed_cost_hub_2":"real","fixed_cost_hub_3":"real","fixed_cost_hub_4":"real","response_time":"real[19][5]"},"derived":{"fixed_cost[j]":"params['fixed_cost_hub_'+str(j)]"},"variables":{"hub_open[j]":"binary, j in J","assigned[i,j]":"binary, (i,j) in I x J"},"constraints":["sum(assigned[i,j] for j in J) == 1, for each i in I","assigned[i,j] <= hub_open[j], for each (i,j) in I x J"],"objective":"minimize sum(fixed_cost[j]*hub_open[j] for j in J) + sum(response_time[i,j]*assigned[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.incidents = pyo.RangeSet(0, 18)
    model.hubs = pyo.RangeSet(0, 4)

    fixed_costs = {
        0: params["fixed_cost_hub_0"],
        1: params["fixed_cost_hub_1"],
        2: params["fixed_cost_hub_2"],
        3: params["fixed_cost_hub_3"],
        4: params["fixed_cost_hub_4"],
    }
    response_times = params["response_time"]

    model.fixed_cost = pyo.Param(
        model.hubs,
        initialize=fixed_costs,
        within=pyo.Reals,
    )
    model.response_time = pyo.Param(
        model.incidents,
        model.hubs,
        initialize={
            (i, j): response_times[i][j]
            for i in model.incidents
            for j in model.hubs
        },
        within=pyo.Reals,
    )

    model.hub_open = pyo.Var(model.hubs, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.incidents, model.hubs, domain=pyo.Binary
    )

    def serve_once_rule(instance, i):
        return sum(
            instance.assigned[i, j] for j in instance.hubs
        ) == 1

    model.serve_once = pyo.Constraint(
        model.incidents, rule=serve_once_rule
    )

    def activated_hub_rule(instance, i, j):
        return instance.assigned[i, j] <= instance.hub_open[j]

    model.activated_hub = pyo.Constraint(
        model.incidents, model.hubs, rule=activated_hub_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[j] * model.hub_open[j]
            for j in model.hubs
        )
        + sum(
            model.response_time[i, j] * model.assigned[i, j]
            for i in model.incidents
            for j in model.hubs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}