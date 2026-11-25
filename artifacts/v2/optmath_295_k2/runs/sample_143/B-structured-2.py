# IR: {"sets":{"I":"0..7","J":"0..6"},"params":{"supply":"supply[i]","demand":"demand[j]","cost":"cost[i,j], nested 8x7 or flat row-major","capacity":"capacity[i,j], nested 8x7 or flat row-major"},"variables":{"flow[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, flow[i,j]) = supply[i] for each i in I","sum(i in I, flow[i,j]) = demand[j] for each j in J","flow[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, cost[i,j] * flow[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    def matrix_entry(data, i, j):
        if len(data) == 8:
            return data[i][j]
        return data[7 * i + j]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 7)
    model.J = pyo.RangeSet(0, 6)

    model.supply_amount = pyo.Param(
        model.I, initialize=lambda mdl, i: supply[i]
    )
    model.demand_amount = pyo.Param(
        model.J, initialize=lambda mdl, j: demand[j]
    )
    model.unit_cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: matrix_entry(cost, i, j),
    )
    model.arc_capacity = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: matrix_entry(capacity, i, j),
    )

    model.flow = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.supply_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(mdl.flow[i, j] for j in mdl.J)
        == mdl.supply_amount[i],
    )
    model.demand_balance = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: sum(mdl.flow[i, j] for i in mdl.I)
        == mdl.demand_amount[j],
    )
    model.capacity_limit = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: mdl.flow[i, j] <= mdl.arc_capacity[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.flow[i, j]
            for i in model.I
            for j in model.J
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