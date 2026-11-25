# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"supply":"supply[i]","demand":"demand[j]","cost":"cost[i][j] or cost[i,j]","capacity":"capacity[i][j] or capacity[i,j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum_j shipment[i,j] = supply[i] for each i","sum_i shipment[i,j] = demand[j] for each j","shipment[i,j] <= capacity[i,j] for each i,j"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept indexed supply/demand and nested or tuple-keyed cost/capacity."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    def matrix_entry(data, i, j):
        if isinstance(data, dict) and (i, j) in data:
            return data[i, j]
        return data[i][j]

    model = pyo.ConcreteModel()
    model.warehouses = pyo.RangeSet(0, 3)
    model.stores = pyo.RangeSet(0, 4)

    model.supply_amount = pyo.Param(
        model.warehouses,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand_amount = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: matrix_entry(cost, i, j),
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: matrix_entry(capacity, i, j),
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            == mdl.supply_amount[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.warehouses)
            == mdl.demand_amount[j]
        )

    def capacity_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.route_capacity[i, j]

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.capacity_limit = pyo.Constraint(
        model.warehouses, model.stores, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.shipment[i, j]
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