import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]
    capacities = params["capacities"]

    num_warehouses = len(supplies)
    num_stores = len(demands)

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, num_warehouses - 1)
    model.stores = pyo.RangeSet(0, num_stores - 1)

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def cap_rule(model, i, j):
        return model.shipment[i, j] <= capacities[i][j]

    model.capacity_limit = pyo.Constraint(
        model.warehouses, model.stores, rule=cap_rule
    )

    def supply_rule(model, i):
        return sum(model.shipment[i, j] for j in model.stores) == supplies[i]

    model.supply_limit = pyo.Constraint(model.warehouses, rule=supply_rule)

    def demand_rule(model, j):
        return sum(model.shipment[i, j] for i in model.warehouses) == demands[j]

    model.demand_requirement = pyo.Constraint(model.stores, rule=demand_rule)

    def obj_rule(model):
        return sum(
            transport_costs[i][j] * model.shipment[i, j]
            for i in model.warehouses
            for j in model.stores
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "no feasible solution"}

    return {"objective": obj_val, "status": "optimal"}