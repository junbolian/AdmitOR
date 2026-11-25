# IR: {"sets":{"O":"0..5","D":"0..4","P":"0..1"},"params":{"supply":"supply[O,P]","demand":"demand[D,P]","cost":"cost[O,D,P]","limit":"limit[O,D]"},"variables":{"x[O,D,P]":"continuous, nonnegative"},"constraints":["sum(j in D) x[i,j,k] = supply[i,k] for i in O, k in P","sum(i in O) x[i,j,k] = demand[j,k] for j in D, k in P","sum(k in P) x[i,j,k] <= limit[i,j] for i in O, j in D"],"objective":"minimize sum(i in O,j in D,k in P) cost[i,j,k]*x[i,j,k]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    model = pyo.ConcreteModel()

    model.O = pyo.RangeSet(0, 5)
    model.D = pyo.RangeSet(0, 4)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.O,
        model.P,
        initialize=lambda mdl, i, k: supply[i][k],
    )
    model.demand = pyo.Param(
        model.D,
        model.P,
        initialize=lambda mdl, j, k: demand[j][k],
    )
    model.cost = pyo.Param(
        model.O,
        model.D,
        model.P,
        initialize=lambda mdl, i, j, k: cost[i][j][k],
    )
    model.route_limit = pyo.Param(
        model.O,
        model.D,
        initialize=lambda mdl, i, j: limit[i][j],
    )

    model.x = pyo.Var(
        model.O,
        model.D,
        model.P,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i, k):
        return sum(mdl.x[i, j, k] for j in mdl.D) == mdl.supply[i, k]

    model.supply_balance = pyo.Constraint(
        model.O, model.P, rule=supply_rule
    )

    def demand_rule(mdl, j, k):
        return sum(mdl.x[i, j, k] for i in mdl.O) == mdl.demand[j, k]

    model.demand_balance = pyo.Constraint(
        model.D, model.P, rule=demand_rule
    )

    def capacity_rule(mdl, i, j):
        return (
            sum(mdl.x[i, j, k] for k in mdl.P)
            <= mdl.route_limit[i, j]
        )

    model.route_capacity = pyo.Constraint(
        model.O, model.D, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j, k] * model.x[i, j, k]
            for i in model.O
            for j in model.D
            for k in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises when an infeasible solve cannot load a solution.
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}