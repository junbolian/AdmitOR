# IR: {
#   "sets": {"I": [0, 1, 2, 3, 4, 5, 6], "J": [0, 1, 2, 3, 4, 5]},
#   "params": {"supply[i]": "params['supply_'+str(i)]", "demand[j]": "params['demand_'+str(j)]", "cost[i,j]": "params['cost_'+str(i)][j]", "cap[i,j]": "params['cap_'+str(i)][j]"},
#   "decision_variables": {"x[i,j]": "continuous nonnegative, i in I, j in J"},
#   "constraints": [
#     "sum(x[i,j] for j in J) <= supply[i] for each i in I",
#     "sum(x[i,j] for i in I) == demand[j] for each j in J",
#     "x[i,j] <= cap[i,j] for each i in I, j in J"
#   ],
#   "objective": "minimize sum(cost[i,j]*x[i,j] for i in I for j in J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 6)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I,
        initialize={i: params[f"supply_{i}"] for i in model.I},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: params[f"demand_{j}"] for j in model.J},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params[f"cost_{i}"][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )
    model.cap = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params[f"cap_{i}"][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(block, i):
        return sum(block.x[i, j] for j in block.J) <= block.supply[i]

    model.supply_limits = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(block, j):
        return sum(block.x[i, j] for i in block.I) == block.demand[j]

    model.demand_requirements = pyo.Constraint(model.J, rule=demand_rule)

    def transport_rule(block, i, j):
        return block.x[i, j] <= block.cap[i, j]

    model.transport_limits = pyo.Constraint(
        model.I, model.J, rule=transport_rule
    )

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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}