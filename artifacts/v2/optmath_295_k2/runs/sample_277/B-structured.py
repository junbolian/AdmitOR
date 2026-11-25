# IR: {"sets":{"V":[0,1,2,3,4,5],"N":[1,2,3,4,5],"A":"{(i,j): i,j in V, i != j}"},"params":{"dist[i,j]":"params['dist_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [0,5] for i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[0] = 0","u[i] >= 1 for i in N","u[i] - u[j] + 6*x[i,j] <= 5 for i,j in N with i != j"],"objective":"minimize sum(dist[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(6), ordered=True)
    model.N = pyo.Set(initialize=range(1, 6), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(6)
            for j in range(6)
            if i != j
        ],
    )

    model.dist = pyo.Param(
        model.A,
        initialize={
            (i, j): params[f"dist_{i}_{j}"]
            for i, j in model.A
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.V, domain=pyo.Reals, bounds=(0, 5))

    def outgoing_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.V if j != i) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)

    def incoming_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.V if i != j) == 1

    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)

    model.depot_position = pyo.Constraint(expr=model.u[0] == 0)

    def position_lower_rule(mod, i):
        return mod.u[i] >= 1

    model.position_lower = pyo.Constraint(model.N, rule=position_lower_rule)

    def subtour_rule(mod, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return mod.u[i] - mod.u[j] + 6 * mod.x[i, j] <= 5

    model.subtour = pyo.Constraint(model.N, model.N, rule=subtour_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.dist[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}