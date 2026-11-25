# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_costs":{"index":"F","type":"NonNegativeReals","source":"params['fixed_costs']"},"demands":{"index":"C","type":"NonNegativeReals","source":"params['demands']"},"shipping_costs":{"index":"F x C","type":"NonNegativeReals","source":"params['shipping_costs']"},"capacities":{"index":"F","type":"NonNegativeReals","source":"params['capacities']"}},"variables":{"opened":{"index":"F","type":"Binary"},"shipment":{"index":"F x C","type":"NonNegativeReals"}},"constraints":["For each j in C: sum(shipment[i,j] for i in F) == demands[j]","For each i in F: sum(shipment[i,j] for j in C) <= capacities[i] * opened[i] (joint activation and capacity limit)"],"objective":{"sense":"minimize","expression":"sum(fixed_costs[i] * opened[i] for i in F) + sum(shipping_costs[i,j] * shipment[i,j] for i in F for j in C)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 9)

    model.fixed_costs = pyo.Param(
        model.F,
        initialize={i: fixed_costs[i] for i in model.F},
        within=pyo.NonNegativeReals,
    )
    model.demands = pyo.Param(
        model.C,
        initialize={j: demands[j] for j in model.C},
        within=pyo.NonNegativeReals,
    )
    model.shipping_costs = pyo.Param(
        model.F,
        model.C,
        initialize={
            (i, j): shipping_costs[i][j]
            for i in model.F
            for j in model.C
        },
        within=pyo.NonNegativeReals,
    )
    model.capacities = pyo.Param(
        model.F,
        initialize={i: capacities[i] for i in model.F},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.F, model.C, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.F)
            == instance.demands[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.C, rule=demand_rule
    )

    def capacity_activation_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.C)
            <= instance.capacities[i] * instance.opened[i]
        )

    model.capacity_activation = pyo.Constraint(
        model.F, rule=capacity_activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_costs[i] * model.opened[i]
                for i in model.F
            )
            + sum(
                model.shipping_costs[i, j] * model.shipment[i, j]
                for i in model.F
                for j in model.C
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