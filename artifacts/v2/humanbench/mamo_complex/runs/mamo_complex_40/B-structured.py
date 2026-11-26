# IR: {"sets":{"C":"range(params['num_centers'])","S":"range(params['num_stores'])"},"params":{"opening_cost":"opening_cost[c]","transport_cost":"transport_cost[c][s]","demand":"demand[s]","capacity":"capacity[c]","num_centers":"frozen center count","num_stores":"frozen store count"},"variables":{"opened[c]":"binary","shipment[c,s]":"nonnegative continuous"},"constraints":["For each s: sum_c shipment[c,s] == demand[s]","For each c: sum_s shipment[c,s] <= capacity[c] * opened[c]"],"objective":"minimize sum_c opening_cost[c]*opened[c] + sum_c,s transport_cost[c][s]*shipment[c,s]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=range(num_centers), ordered=True)
    model.S = pyo.Set(initialize=range(num_stores), ordered=True)

    model.opening_cost = pyo.Param(
        model.C,
        initialize=lambda mdl, c: opening_cost[c],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.C,
        model.S,
        initialize=lambda mdl, c, s: transport_cost[c][s],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.S,
        initialize=lambda mdl, s: demand[s],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.C,
        initialize=lambda mdl, c: capacity[c],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.C, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.C, model.S, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, s):
        return (
            sum(mdl.shipment[c, s] for c in mdl.C)
            == mdl.demand[s]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.S, rule=demand_rule
    )

    def capacity_rule(mdl, c):
        return (
            sum(mdl.shipment[c, s] for s in mdl.S)
            <= mdl.capacity[c] * mdl.opened[c]
        )

    model.center_capacity = pyo.Constraint(
        model.C, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[c] * model.opened[c]
                for c in model.C
            )
            + sum(
                model.transport_cost[c, s] * model.shipment[c, s]
                for c in model.C
                for s in model.S
            )
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