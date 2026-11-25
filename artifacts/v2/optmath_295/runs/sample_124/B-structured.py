# IR:
# {
#   "sets": {"individuals": "0..7", "projects": "0..7"},
#   "params": {"costs": "real[8,8]", "supply": "nonnegative_real[8]", "demand": "nonnegative_real[8]", "capacity_limits": "nonnegative_real[8,8]"},
#   "decision_variables": {"allocation[i,j]": "nonnegative continuous"},
#   "constraints": [
#     "For each individual i: sum_j allocation[i,j] = supply[i]",
#     "For each project j: sum_i allocation[i,j] = demand[j]",
#     "For each pair (i,j): allocation[i,j] <= capacity_limits[i,j]"
#   ],
#   "objective": "minimize sum_i sum_j costs[i,j] * allocation[i,j]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]

    model = pyo.ConcreteModel()
    model.individuals = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 7)

    model.assignment_cost = pyo.Param(
        model.individuals,
        model.projects,
        initialize=lambda mdl, i, j: costs[i][j],
        within=pyo.Reals,
    )
    model.person_supply = pyo.Param(
        model.individuals,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.pair_capacity = pyo.Param(
        model.individuals,
        model.projects,
        initialize=lambda mdl, i, j: capacity_limits[i][j],
        within=pyo.NonNegativeReals,
    )

    model.allocation = pyo.Var(
        model.individuals,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.individuals,
        rule=lambda mdl, i: sum(
            mdl.allocation[i, j] for j in mdl.projects
        ) == mdl.person_supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: sum(
            mdl.allocation[i, j] for i in mdl.individuals
        ) == mdl.project_demand[j],
    )
    model.capacity_bound = pyo.Constraint(
        model.individuals,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.allocation[i, j] <= mdl.pair_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.allocation[i, j]
            for i in model.individuals
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}