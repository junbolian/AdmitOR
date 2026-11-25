# IR: {
#   "sets": {"warehouses": "range(8)", "stores": "range(6)"},
#   "params": {"supplies": "params['supplies'][i]", "demands": "params['demands'][j]", "transport_costs": "params['transport_costs'][i][j]", "capacities": "params['capacities'][i][j]"},
#   "variables": {"shipment[i,j]": "continuous nonnegative"},
#   "constraints": [
#     "sum(shipment[i,j] for j in stores) == supplies[i] for each warehouse i",
#     "sum(shipment[i,j] for i in warehouses) == demands[j] for each store j",
#     "shipment[i,j] <= capacities[i,j] for each warehouse i and store j"
#   ],
#   "objective": "minimize sum(transport_costs[i,j] * shipment[i,j] for i in warehouses for j in stores)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.warehouses = pyo.Set(initialize=range(8), ordered=True)
    model.stores = pyo.Set(initialize=range(6), ordered=True)

    model.supply_data = pyo.Param(
        model.warehouses,
        initialize={i: supplies[i] for i in model.warehouses},
        within=pyo.Reals,
    )
    model.demand_data = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in model.stores},
        within=pyo.Reals,
    )
    model.cost_data = pyo.Param(
        model.warehouses,
        model.stores,
        initialize={
            (i, j): transport_costs[i][j]
            for i in model.warehouses
            for j in model.stores
        },
        within=pyo.Reals,
    )
    model.capacity_data = pyo.Param(
        model.warehouses,
        model.stores,
        initialize={
            (i, j): capacities[i][j]
            for i in model.warehouses
            for j in model.stores
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(block, i):
        return (
            sum(block.shipment[i, j] for j in block.stores)
            == block.supply_data[i]
        )

    def demand_rule(block, j):
        return (
            sum(block.shipment[i, j] for i in block.warehouses)
            == block.demand_data[j]
        )

    def capacity_rule(block, i, j):
        return block.shipment[i, j] <= block.capacity_data[i, j]

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.route_capacity = pyo.Constraint(
        model.warehouses, model.stores, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_data[i, j] * model.shipment[i, j]
            for i in model.warehouses
            for j in model.stores
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