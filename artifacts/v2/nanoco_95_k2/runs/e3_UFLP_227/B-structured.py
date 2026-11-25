# IR: {"sets":{"users":"0..19","locations":"0..4"},"params":{"fixed_cost":"real[locations], from params['fixed_cost']","latency":"real[users,locations], from params['latency']"},"variables":{"opened":"binary[locations]","assigned":"binary[users,locations]"},"constraints":["For each user i: sum_j assigned[i,j] = 1.","For each user i and location j: assigned[i,j] <= opened[j]."],"objective":"Minimize sum_j fixed_cost[j]*opened[j] + sum_i sum_j latency[i,j]*assigned[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    latency = params["latency"]

    model = pyo.ConcreteModel()

    model.users = pyo.RangeSet(0, 19)
    model.locations = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.locations,
        initialize=lambda mdl, j: fixed_cost[j],
        within=pyo.Reals,
    )
    model.latency = pyo.Param(
        model.users,
        model.locations,
        initialize=lambda mdl, i, j: latency[i][j],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.locations, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.users, model.locations, domain=pyo.Binary
    )

    def assignment_rule(mdl, i):
        return sum(mdl.assigned[i, j] for j in mdl.locations) == 1

    model.exactly_one_assignment = pyo.Constraint(
        model.users, rule=assignment_rule
    )

    def activation_rule(mdl, i, j):
        return mdl.assigned[i, j] <= mdl.opened[j]

    model.assignment_requires_activation = pyo.Constraint(
        model.users, model.locations, rule=activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[j] * model.opened[j]
                for j in model.locations
            )
            + sum(
                model.latency[i, j] * model.assigned[i, j]
                for i in model.users
                for j in model.locations
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave success determination to objective evaluation below.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}