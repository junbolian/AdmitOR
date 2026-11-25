# IR: {"sets":{"warehouses":[0,1,2,3,4,5],"stores":[0,1,2,3,4,5]},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["For each warehouse i: sum_j shipment[i,j] == supply[i].","For each store j: sum_i shipment[i,j] == demand[j]."],"objective":"Minimize sum_i sum_j cost[i,j] * shipment[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 5)

    model.available_supply = pyo.Param(
        model.warehouses,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            == mdl.available_supply[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.warehouses)
            == mdl.required_demand[j]
        )

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
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
    except RuntimeError as exc:
        # APPsi HiGHS raises this when no feasible solution can be loaded.
        # Leave unexpected solver exceptions visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}