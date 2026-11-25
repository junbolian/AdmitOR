# IR: {"sets":{"V":"{0,...,9}","C":"V\\{0}","A":"{(i,j) in V x V: i!=j}","B":"{(i,j) in C x C: i!=j}"},"params":{"distance_matrix":"params['distance_matrix']; 10x10 travel distances","d[i,j]":"distance_matrix[i][j] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real in [1,9] for i in C"},"constraints":{"outgoing":"sum(x[i,j] for j in V if j!=i)=1 for i in V","incoming":"sum(x[i,j] for i in V if i!=j)=1 for j in V","subtour":"u[i]-u[j]+9*x[i,j]<=8 for (i,j) in B"},"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.V = pyo.RangeSet(0, 9)
    model.C = pyo.RangeSet(1, 9)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(10)
            for j in range(10)
            if i != j
        ],
    )
    model.B = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 10)
            for j in range(1, 10)
            if i != j
        ],
    )

    model.d = pyo.Param(
        model.A,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in range(10)
            for j in range(10)
            if i != j
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.C, domain=pyo.Reals, bounds=(1, 9))

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.V if j != i
        ) == 1

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.V if i != j
        ) == 1

    def subtour_rule(instance, i, j):
        return (
            instance.u[i] - instance.u[j] + 9 * instance.x[i, j]
            <= 8
        )

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)
    model.subtour = pyo.Constraint(model.B, rule=subtour_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.d[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}