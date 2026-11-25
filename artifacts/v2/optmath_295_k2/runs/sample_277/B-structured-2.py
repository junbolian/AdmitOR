# IR: {"sets":{"C":[0,1,2,3,4,5],"A":"{(i,j) in C x C: i != j}","N":"C \\ {0}"},"params":{"dist[i,j]":"params['dist_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [0,5] for i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","u[0] = 0","u[i] >= 1 for i in N","u[j] >= u[i] + 1 - 6*(1-x[i,j]) for i,j in N with i != j"],"objective":"minimize sum(dist[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=range(6), ordered=True)
    model.N = pyo.Set(initialize=range(1, 6), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(6) for j in range(6) if i != j],
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
    model.u = pyo.Var(model.C, domain=pyo.Reals, bounds=(0, 5))

    def outgoing_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.C if j != i) == 1

    model.outgoing = pyo.Constraint(model.C, rule=outgoing_rule)

    def incoming_rule(instance, j):
        return sum(instance.x[i, j] for i in instance.C if i != j) == 1

    model.incoming = pyo.Constraint(model.C, rule=incoming_rule)

    model.depot_position = pyo.Constraint(expr=model.u[0] == 0)
    model.non_depot_position = pyo.Constraint(
        model.N, rule=lambda instance, i: instance.u[i] >= 1
    )

    # Exclude the depot from ordering constraints so the tour can return to it.
    def ordering_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[j]
            >= instance.u[i] + 1 - 6 * (1 - instance.x[i, j])
        )

    model.ordering = pyo.Constraint(model.N, model.N, rule=ordering_rule)

    model.total_distance = pyo.Objective(
        expr=sum(model.dist[i, j] * model.x[i, j] for i, j in model.A),
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