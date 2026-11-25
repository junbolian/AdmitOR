# IR: {"sets":{"warehouses":[0,1,2,3,4],"stores":[0,1,2,3]},"params":{"supply":"warehouse vector from params['supply']","demand":"store vector from params['demand']","cost":"warehouse-store matrix from params['cost']","capacity":"warehouse-store matrix from params['capacity']"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum_j shipment[i,j] = supply[i] for every warehouse i","sum_i shipment[i,j] = demand[j] for every store j","shipment[i,j] <= capacity[i,j] for every route (i,j)"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.warehouses = pyo.RangeSet(0, 4)
    model.stores = pyo.RangeSet(0, 3)

    model.supply = pyo.Param(
        model.warehouses,
        initialize={i: supply[i] for i in model.warehouses},
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={j: demand[j] for j in model.stores},
    )
    model.cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize={
            (i, j): cost[i][j]
            for i in model.warehouses
            for j in model.stores
        },
    )
    model.capacity = pyo.Param(
        model.warehouses,
        model.stores,
        initialize={
            (i, j): capacity[i][j]
            for i in model.warehouses
            for j in model.stores
        },
    )

    model.shipment = pyo.Var(
        model.warehouses, model.stores, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.warehouses)
            == instance.demand[j]
        )

    def capacity_rule(instance, i, j):
        return instance.shipment[i, j] <= instance.capacity[i, j]

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
            model.cost[i, j] * model.shipment[i, j]
            for i in model.warehouses
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}