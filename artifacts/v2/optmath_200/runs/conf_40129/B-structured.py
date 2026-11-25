# IR: {"sets":{"F":["facility_0", "...", "facility_7"],"C":["customer_0", "...", "customer_6"]},"params":{"fixed_costs":"F -> real","capacities":"F -> nonnegative real","demands":"C -> nonnegative real","shipping_costs":"F x C -> real"},"variables":{"opened[f]":"binary for f in F","shipment[f,c]":"nonnegative continuous for (f,c) in F x C"},"constraints":["For each c in C: sum_f shipment[f,c] = demands[c]","For each f in F: sum_c shipment[f,c] <= capacities[f] * opened[f]"],"objective":"Minimize sum_f fixed_costs[f]*opened[f] + sum_f,c shipping_costs[f,c]*shipment[f,c]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept vectors and shipping rows as sequences or label-keyed mappings."""
    facilities = [f"facility_{i}" for i in range(8)]
    customers = [f"customer_{j}" for j in range(7)]

    fixed_costs = params["fixed_costs"]
    capacities = params["capacities"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]

    def entry(data, label, position):
        return data[label] if isinstance(data, Mapping) else data[position]

    fixed_data = {
        facility: entry(fixed_costs, facility, i)
        for i, facility in enumerate(facilities)
    }
    capacity_data = {
        facility: entry(capacities, facility, i)
        for i, facility in enumerate(facilities)
    }
    demand_data = {
        customer: entry(demands, customer, j)
        for j, customer in enumerate(customers)
    }
    shipping_data = {}
    for i, facility in enumerate(facilities):
        row = entry(shipping_costs, facility, i)
        for j, customer in enumerate(customers):
            shipping_data[facility, customer] = entry(row, customer, j)

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=facilities, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)

    model.fixed_cost = pyo.Param(
        model.F, initialize=fixed_data, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.F, initialize=capacity_data, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.C, initialize=demand_data, within=pyo.NonNegativeReals
    )
    model.shipping_cost = pyo.Param(
        model.F, model.C, initialize=shipping_data, within=pyo.Reals
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipment = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(instance, customer):
        return (
            sum(instance.shipment[facility, customer] for facility in instance.F)
            == instance.demand[customer]
        )

    model.demand_fulfillment = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(instance, facility):
        return (
            sum(instance.shipment[facility, customer] for customer in instance.C)
            <= instance.capacity[facility] * instance.opened[facility]
        )

    model.capacity_link = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[facility] * model.opened[facility]
            for facility in model.F
        )
        + sum(
            model.shipping_cost[facility, customer]
            * model.shipment[facility, customer]
            for facility in model.F
            for customer in model.C
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