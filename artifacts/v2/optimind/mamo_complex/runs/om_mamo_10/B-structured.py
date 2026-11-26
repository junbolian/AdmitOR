# IR: {"sets":{"centers":"1..6","stores":"1..4"},"params":{"opening_costs":"real[centers]","transport_costs":"real[centers,stores]","demands":"nonnegative_real[stores]","capacities":"nonnegative_real[centers]"},"variables":{"opened":"binary[centers]","shipment":"nonnegative_real[centers,stores]"},"constraints":["For each store j: sum_i shipment[i,j] == demands[j]","For each center i: sum_j shipment[i,j] <= capacities[i] * opened[i]"],"objective":"minimize sum_i opening_costs[i]*opened[i] + sum_i,j transport_costs[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences for vectors and matrix rows."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 6)
    model.stores = pyo.RangeSet(1, 4)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda _, i: opening_costs[i - 1],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda _, i, j: transport_costs[i - 1][j - 1],
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize=lambda _, j: demands[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize=lambda _, i: capacities[i - 1],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.centers)
            == instance.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[i] * model.opened[i]
            for i in model.centers
        )
        + sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.centers
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}