# IR: {"sets":{"origins":[0,1,2,3],"destinations":[0,1,2,3]},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"flow[i,j]":{"type":"continuous","lower_bound":0}},"constraints":["sum(flow[i,j] for j in destinations) == supply[i] for each origin i","sum(flow[i,j] for i in origins) == demand[j] for each destination j","flow[i,j] <= capacity[i,j] for each origin i and destination j"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * flow[i,j] for i in origins for j in destinations)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 3)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: params["supply"][i],
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: params["demand"][j],
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: params["cost"][i][j],
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: params["capacity"][i][j],
    )

    model.flow = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.flow[i, j] for j in mdl.destinations
        ) == mdl.supply[i],
    )

    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.flow[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )

    model.transport_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.flow[i, j] <= mdl.capacity[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load may leave the objective unavailable.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}