# IR: {"sets":{"F":"range(params['num_facilities'])","S":"range(params['num_stores'])"},"params":{"fixed_cost":"facility-indexed opening costs","shipping_cost_row0":"facility-indexed unit shipping costs to store 0, assumed identical across all stores because no other shipping costs are supplied","demand":"store-indexed demands","capacity":"facility-indexed capacities","num_facilities":"frozen facility count","num_stores":"frozen store count"},"variables":{"opened[f]":"Binary","shipment[f,s]":"NonNegativeReals"},"constraints":["For each s in S: sum(shipment[f,s] for f in F) == demand[s]","For each f in F: sum(shipment[f,s] for s in S) <= capacity[f]*opened[f]"],"objective":"Minimize sum(fixed_cost[f]*opened[f] for f in F) + sum(shipping_cost_row0[f]*shipment[f,s] for f in F for s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    num_stores = params["num_stores"]
    fixed_cost = params["fixed_cost"]
    shipping_cost_row0 = params["shipping_cost_row0"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=range(num_facilities), ordered=True)
    model.S = pyo.Set(initialize=range(num_stores), ordered=True)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={f: fixed_cost[f] for f in model.F},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.F,
        initialize={f: shipping_cost_row0[f] for f in model.F},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.S,
        initialize={s: demand[s] for s in model.S},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.F,
        initialize={f: capacity[f] for f in model.F},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipment = pyo.Var(model.F, model.S, domain=pyo.NonNegativeReals)

    def demand_rule(instance, s):
        return (
            sum(instance.shipment[f, s] for f in instance.F)
            == instance.demand[s]
        )

    model.demand_balance = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(instance, f):
        return (
            sum(instance.shipment[f, s] for s in instance.S)
            <= instance.capacity[f] * instance.opened[f]
        )

    model.capacity_limit = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[f] * model.opened[f] for f in model.F)
            + sum(
                model.shipping_cost[f] * model.shipment[f, s]
                for f in model.F
                for s in model.S
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        # Continue to the objective retrieval check; no solution was loaded.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}