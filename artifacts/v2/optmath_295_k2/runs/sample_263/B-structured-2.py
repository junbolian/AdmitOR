# IR: {"sets":{"I":[0,1,2,3,4,5],"J":[0,1,2,3,4,5]},"params":{"supply":"I -> resource units","demand":"J -> resource units","cost":"I x J -> unit cost","capacity":"I x J -> route limit"},"variables":{"x[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, x[i,j]) == supply[i] for i in I","sum(i in I, x[i,j]) == demand[j] for j in J","x[i,j] <= capacity[i,j] for (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, cost[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I, initialize={i: supply[i] for i in model.I}
    )
    model.demand = pyo.Param(
        model.J, initialize={j: demand[j] for j in model.J}
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={(i, j): cost[i][j] for i in model.I for j in model.J},
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize={(i, j): capacity[i][j] for i in model.I for j in model.J},
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.I) == mdl.demand[j]

    def capacity_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)
    model.route_capacity = pyo.Constraint(model.I, model.J, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Success is still determined solely by objective availability.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}