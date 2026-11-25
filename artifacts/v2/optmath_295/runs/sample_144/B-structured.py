# IR: {"sets":{"W":"0..11","S":"0..13"},"params":{"supply":"params['supply'][i], i in W","demand":"params['demand'][j], j in S","transport_cost":"params['transport_cost'][i][j], (i,j) in W x S"},"variables":{"shipment[i,j]":"NonNegativeReals, (i,j) in W x S"},"constraints":["sum(shipment[i,j] for j in S) == supply[i], for each i in W","sum(shipment[i,j] for i in W) == demand[j], for each j in S"],"objective":"minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in W x S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, 11)
    model.S = pyo.RangeSet(0, 13)

    model.supply = pyo.Param(
        model.W,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.S,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.W,
        model.S,
        initialize=lambda mdl, i, j: transport_cost[i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.W, model.S, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, i):
        return sum(mdl.shipment[i, j] for j in mdl.S) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.W) == mdl.demand[j]

    model.supply_balance = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.S, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.W
            for j in model.S
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi HiGHS raises when it cannot load a feasible solution.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}