# IR: {"sets":{"centers":"1..6","stores":"1..7"},"params":{"opening_costs":"opening_costs[i-1]","transport_costs":"transport_costs[i-1][j-1]","demands":"demands[j-1]","supply_capacities":"supply_capacities[i-1]"},"variables":{"opened[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each store j: sum_i shipment[i,j] = demands[j-1]","For each center i: sum_j shipment[i,j] <= supply_capacities[i-1] * opened[i]"],"objective":"minimize sum_i opening_costs[i-1] * opened[i] + sum_i,j transport_costs[i-1][j-1] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    supply_capacities = params["supply_capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 6)
    model.stores = pyo.RangeSet(1, 7)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize={i: opening_costs[i - 1] for i in model.centers},
    )
    model.unit_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_costs[i - 1][j - 1]
            for i in model.centers
            for j in model.stores
        },
    )
    model.required_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j - 1] for j in model.stores},
    )
    model.supply_limit = pyo.Param(
        model.centers,
        initialize={i: supply_capacities[i - 1] for i in model.centers},
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.centers)
            == instance.required_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.supply_limit[i] * instance.opened[i]
        )

    model.capacity_link = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[i] * model.opened[i] for i in model.centers)
            + sum(
                model.unit_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
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