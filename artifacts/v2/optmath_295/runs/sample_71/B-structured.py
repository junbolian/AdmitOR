# IR: {"sets":{"F":"0..5","C":"0..8"},"params":{"fixed_costs":"F","shipping_costs":"C x F","demands":"C","capacities":"F"},"variables":{"opened[f]":"binary","shipped[c,f]":"nonnegative continuous"},"constraints":["forall c in C: sum(f in F, shipped[c,f]) = demands[c]","forall f in F: sum(c in C, shipped[c,f]) <= capacities[f] * opened[f]"],"objective":"minimize sum(f in F, fixed_costs[f] * opened[f]) + sum(c in C, f in F, shipping_costs[c,f] * shipped[c,f])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 5)
    model.customers = pyo.RangeSet(0, 8)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={
            facility: params["fixed_costs"][facility]
            for facility in model.facilities
        },
    )
    model.shipping_cost = pyo.Param(
        model.customers,
        model.facilities,
        initialize={
            (customer, facility): params["shipping_costs"][customer][facility]
            for customer in model.customers
            for facility in model.facilities
        },
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={
            customer: params["demands"][customer]
            for customer in model.customers
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={
            facility: params["capacities"][facility]
            for facility in model.facilities
        },
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.customers,
        model.facilities,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(model, customer):
        return sum(
            model.shipped[customer, facility]
            for facility in model.facilities
        ) == model.demand[customer]

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(model, facility):
        return sum(
            model.shipped[customer, facility]
            for customer in model.customers
        ) <= model.capacity[facility] * model.opened[facility]

    model.capacity_activation = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[facility] * model.opened[facility]
                for facility in model.facilities
            )
            + sum(
                model.shipping_cost[customer, facility]
                * model.shipped[customer, facility]
                for customer in model.customers
                for facility in model.facilities
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}