# IR: {"sets":{"V":[0,1,2,3,4],"N":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","B":"{(i,j) in N x N: i != j}"},"params":{"distance[i,j]":"params['dist_i_j'] for (i,j) in A","lower":"params['u_min']","upper":"params['u_max']","M":"max(0, upper-lower+1)"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"real with lower <= u[i] <= upper, i in N"},"constraints":["sum(x[i,j] for j != i) = 1 for every i in V","sum(x[i,j] for i != j) = 1 for every j in V","u[j]-u[i] >= 1-M*(1-x[i,j]) for every (i,j) in B","u[j]-u[i] <= 1+M*(1-x[i,j]) for every (i,j) in B"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)","notes":"Exact position increments exclude nondepot subtours; degree constraints then imply one depot tour and distinct nondepot positions."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = range(5)
    nondepot = range(1, 5)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    internal_arcs = [(i, j) for i in nondepot for j in nondepot if i != j]

    distances = {
        (i, j): params[f"dist_{i}_{j}"]
        for i, j in arcs
    }
    lower = params["u_min"]
    upper = params["u_max"]
    big_m = max(0, upper - lower + 1)

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.nondepot = pyo.Set(initialize=nondepot, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.internal_arcs = pyo.Set(dimen=2, initialize=internal_arcs)

    model.distance = pyo.Param(model.arcs, initialize=distances)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.nondepot, domain=pyo.Reals, bounds=(lower, upper)
    )

    def departure_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.cities if j != i) == 1

    def arrival_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.cities if i != j) == 1

    def increment_lower_rule(mod, i, j):
        return mod.u[j] - mod.u[i] >= 1 - big_m * (1 - mod.x[i, j])

    def increment_upper_rule(mod, i, j):
        return mod.u[j] - mod.u[i] <= 1 + big_m * (1 - mod.x[i, j])

    model.departure = pyo.Constraint(model.cities, rule=departure_rule)
    model.arrival = pyo.Constraint(model.cities, rule=arrival_rule)
    model.increment_lower = pyo.Constraint(
        model.internal_arcs, rule=increment_lower_rule
    )
    model.increment_upper = pyo.Constraint(
        model.internal_arcs, rule=increment_upper_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}