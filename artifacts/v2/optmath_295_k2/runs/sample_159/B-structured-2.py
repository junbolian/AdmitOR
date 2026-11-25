# IR: {"sets":{"C":[0,1,2,3,4],"N":[1,2,3,4],"A":"{(i,j) in C x C: i != j}","P":"{(i,j) in N x N: i != j}"},"params":{"cost[i,j]":"params['cost_i_j'] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Integer in [1,4] for i in N; City 0 has no position variable"},"constraints":["Departure: sum(x[i,j] for j in C if j != i) == 1 for i in C","Arrival: sum(x[i,j] for i in C if i != j) == 1 for j in C","Position: u[j] >= u[i] + 1 - 4*(1-x[i,j]) for (i,j) in P; together with arrival/departure constraints, eliminates subtours and ensures distinct positions"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = range(5)
    nonroot_cities = range(1, 5)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    position_pairs = [
        (i, j)
        for i in nonroot_cities
        for j in nonroot_cities
        if i != j
    ]

    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (0, 4): params["cost_0_4"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 0): params["cost_4_0"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=cities, ordered=True)
    model.N = pyo.Set(initialize=nonroot_cities, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs)
    model.P = pyo.Set(dimen=2, initialize=position_pairs)

    model.cost = pyo.Param(model.A, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.N, domain=pyo.Integers, bounds=(1, 4))

    def departure_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.C if j != i) == 1

    def arrival_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.C if i != j) == 1

    def position_rule(mod, i, j):
        return mod.u[j] >= mod.u[i] + 1 - 4 * (1 - mod.x[i, j])

    model.departure = pyo.Constraint(model.C, rule=departure_rule)
    model.arrival = pyo.Constraint(model.C, rule=arrival_rule)
    model.position_order = pyo.Constraint(model.P, rule=position_rule)

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i, j] * model.x[i, j] for i, j in model.A),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions are allowed to propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}