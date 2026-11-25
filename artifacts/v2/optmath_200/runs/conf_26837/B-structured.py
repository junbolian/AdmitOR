# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6]},"params":{"fixed_costs":"F-indexed nonnegative costs from params","shipping_cost_matrix":"F-by-C nonnegative costs from params","demands":"C-indexed nonnegative demands from params","capacities":"F-indexed nonnegative capacities from params"},"variables":{"opened[f]":"Binary for f in F","shipment[f,c]":"NonNegativeReals for (f,c) in F x C"},"constraints":["sum(shipment[f,c] for f in F) == demands[c] for c in C","sum(shipment[f,c] for c in C) <= capacities[f]*opened[f] for f in F"],"objective":"minimize sum(fixed_costs[f]*opened[f] for f in F) + sum(shipping_cost_matrix[f,c]*shipment[f,c] for (f,c) in F x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based sequences for vectors and a nested cost matrix."""
    fixed_costs = params["fixed_costs"]
    shipping_cost_matrix = params["shipping_cost_matrix"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 6)

    model.fixed_costs = pyo.Param(
        model.F,
        initialize=lambda mdl, facility: fixed_costs[facility],
        within=pyo.NonNegativeReals,
    )
    model.shipping_costs = pyo.Param(
        model.F,
        model.C,
        initialize=lambda mdl, facility, customer: shipping_cost_matrix[facility][customer],
        within=pyo.NonNegativeReals,
    )
    model.demands = pyo.Param(
        model.C,
        initialize=lambda mdl, customer: demands[customer],
        within=pyo.NonNegativeReals,
    )
    model.capacities = pyo.Param(
        model.F,
        initialize=lambda mdl, facility: capacities[facility],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipment = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(mdl, customer):
        return (
            sum(mdl.shipment[facility, customer] for facility in mdl.F)
            == mdl.demands[customer]
        )

    model.demand_fulfillment = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(mdl, facility):
        return (
            sum(mdl.shipment[facility, customer] for customer in mdl.C)
            <= mdl.capacities[facility] * mdl.opened[facility]
        )

    model.capacity_limits = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_costs[facility] * model.opened[facility]
                for facility in model.F
            )
            + sum(
                model.shipping_costs[facility, customer]
                * model.shipment[facility, customer]
                for facility in model.F
                for customer in model.C
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