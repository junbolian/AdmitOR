# IR: {"sets":{"users":"0..19","locations":"0..4"},"params":{"fixed_cost":"fixed_cost[j] from params['fixed_cost']","latency":"latency[i][j] from params['latency']"},"variables":{"opened[j]":"binary","assigned[i,j]":"binary"},"constraints":["For each i: sum_j assigned[i,j] = 1","For each i,j: assigned[i,j] <= opened[j]"],"objective":"Minimize sum_j fixed_cost[j]*opened[j] + sum_i,j latency[i][j]*assigned[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    latency = params["latency"]

    model = pyo.ConcreteModel()
    model.users = pyo.RangeSet(0, 19)
    model.locations = pyo.RangeSet(0, 4)

    model.setup_cost = pyo.Param(
        model.locations,
        initialize=lambda mdl, j: fixed_cost[j],
    )
    model.network_latency = pyo.Param(
        model.users,
        model.locations,
        initialize=lambda mdl, i, j: latency[i][j],
    )

    model.opened = pyo.Var(model.locations, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.users,
        model.locations,
        domain=pyo.Binary,
    )

    def assignment_rule(mdl, i):
        return sum(mdl.assigned[i, j] for j in mdl.locations) == 1

    model.exactly_one_center = pyo.Constraint(
        model.users,
        rule=assignment_rule,
    )

    def activation_rule(mdl, i, j):
        return mdl.assigned[i, j] <= mdl.opened[j]

    model.assignment_requires_activation = pyo.Constraint(
        model.users,
        model.locations,
        rule=activation_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.setup_cost[j] * model.opened[j]
                for j in model.locations
            )
            + sum(
                model.network_latency[i, j] * model.assigned[i, j]
                for i in model.users
                for j in model.locations
            )
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