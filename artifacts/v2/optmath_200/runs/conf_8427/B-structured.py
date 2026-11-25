# IR: {"sets":{"P":[0,1],"I":[0,1,2,3,4,5],"J":[0,1,2,3,4,5]},"params":{"supply_p0_origins":"S[0,i]","supply_p1_origins":"S[1,i]","demand_p0_dests":"D[0,j]","demand_p1_dests":"D[1,j]","cost_p0":"C[0,i,j]","cost_p1":"C[1,i,j]","capacity":"U[i,j]"},"variables":{"x[p,i,j]":"nonnegative continuous"},"constraints":["sum(j in J) x[p,i,j] = S[p,i] for p in P, i in I","sum(i in I) x[p,i,j] = D[p,j] for p in P, j in J","sum(p in P) x[p,i,j] <= U[i,j] for i in I, j in J"],"objective":"minimize sum(p in P,i in I,j in J) C[p,i,j]*x[p,i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = (
        params["supply_p0_origins"],
        params["supply_p1_origins"],
    )
    demand = (
        params["demand_p0_dests"],
        params["demand_p1_dests"],
    )
    cost = (
        params["cost_p0"],
        params["cost_p1"],
    )
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 1)
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 5)

    model.S = pyo.Param(
        model.P, model.I,
        initialize=lambda mdl, p, i: supply[p][i],
    )
    model.D = pyo.Param(
        model.P, model.J,
        initialize=lambda mdl, p, j: demand[p][j],
    )
    model.C = pyo.Param(
        model.P, model.I, model.J,
        initialize=lambda mdl, p, i, j: cost[p][i][j],
    )
    model.U = pyo.Param(
        model.I, model.J,
        initialize=lambda mdl, i, j: capacity[i][j],
    )

    model.x = pyo.Var(
        model.P, model.I, model.J, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, p, i):
        return sum(mdl.x[p, i, j] for j in mdl.J) == mdl.S[p, i]

    def demand_rule(mdl, p, j):
        return sum(mdl.x[p, i, j] for i in mdl.I) == mdl.D[p, j]

    def capacity_rule(mdl, i, j):
        return sum(mdl.x[p, i, j] for p in mdl.P) <= mdl.U[i, j]

    model.supply_balance = pyo.Constraint(
        model.P, model.I, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.P, model.J, rule=demand_rule
    )
    model.arc_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.C[p, i, j] * model.x[p, i, j]
            for p in model.P
            for i in model.I
            for j in model.J
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