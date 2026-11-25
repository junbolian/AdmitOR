# IR: {"sets":{"N":"{0,...,9}","T":"N\\{0}","A":"{(i,j) in N x N: i != j}"},"params":{"cost_0":"params['cost_0'], length 10","cost_1":"params['cost_1'], length 10","cost_2":"params['cost_2'], length 10","cost_3":"params['cost_3'], length 10","cost_4":"params['cost_4'], length 10","cost_5":"params['cost_5'], length 10","cost_6":"params['cost_6'], length 10","cost_7":"params['cost_7'], length 10","cost_8":"params['cost_8'], length 10","cost_9":"params['cost_9'], length 10","c[i,j]":"cost_i[j] for i,j in N"},"variables":{"x[i,j]":"binary for (i,j) in A; selected directed flight leg","u[i]":"continuous in [1,|T|] for i in T; visit order"},"constraints":["sum(x[i,j] for j in N if j != i) = 1 for i in N","sum(x[i,j] for i in N if i != j) = 1 for j in N","u[i] - u[j] + |T|*x[i,j] <= |T|-1 for i,j in T, i != j"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_rows = [
        params["cost_0"],
        params["cost_1"],
        params["cost_2"],
        params["cost_3"],
        params["cost_4"],
        params["cost_5"],
        params["cost_6"],
        params["cost_7"],
        params["cost_8"],
        params["cost_9"],
    ]

    if any(len(row) != 10 for row in cost_rows):
        return {"objective": None, "status": "invalid_cost_dimensions"}

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(0, 9)
    model.T = pyo.RangeSet(1, 9)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.N
            for j in model.N
            if i != j
        ],
    )

    model.c = pyo.Param(
        model.N,
        model.N,
        initialize={
            (i, j): cost_rows[i][j]
            for i in model.N
            for j in model.N
        },
        within=pyo.Reals,
    )

    turbine_count = len(model.T)
    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.T,
        domain=pyo.Reals,
        bounds=(1, turbine_count),
    )

    def outgoing_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.N if j != i) == 1

    def incoming_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.N if i != j) == 1

    def subtour_rule(mod, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mod.u[i] - mod.u[j] + turbine_count * mod.x[i, j]
            <= turbine_count - 1
        )

    model.outgoing = pyo.Constraint(model.N, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.N, rule=incoming_rule)
    model.subtour = pyo.Constraint(model.T, model.T, rule=subtour_rule)

    model.total_energy = pyo.Objective(
        expr=sum(model.c[i, j] * model.x[i, j] for i, j in model.A),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_energy))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}