# IR: {"sets":{"I":"0..7","J":"0..6"},"params":{"supply":"supply[i] from params","demand":"demand[j] from params","cost":"cost[i,j] from params, nested 8x7 or flat row-major","capacity":"capacity[i,j] from params, nested 8x7 or flat row-major"},"variables":{"flow[i,j]":"nonnegative continuous"},"constraints":["sum(flow[i,j] for j in J) == supply[i] for each i in I","sum(flow[i,j] for i in I) == demand[j] for each j in J","flow[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(cost[i,j]*flow[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]
    capacity_data = params["capacity"]

    def matrix_entry(data, i, j):
        if len(data) == 8 * 7:
            return data[i * 7 + j]
        return data[i][j]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 7)
    model.J = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.I,
        initialize=lambda mdl, i: supply_data[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: demand_data[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: matrix_entry(cost_data, i, j),
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: matrix_entry(capacity_data, i, j),
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.supply_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.flow[i, j] for j in mdl.J) == mdl.supply[i]
        ),
    )
    model.demand_balance = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.flow[i, j] for i in mdl.I) == mdl.demand[j]
        ),
    )
    model.route_capacity = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: mdl.flow[i, j] <= mdl.capacity[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}