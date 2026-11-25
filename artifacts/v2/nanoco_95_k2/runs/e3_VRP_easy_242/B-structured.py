# IR: {"sets":{"V":"{0,...,8}","C":"{1,...,8}","A":"{(i,j) in V x V: i != j}"},"params":{"dist_i_j":"params['dist_i_j'] for every 0 <= i < j <= 8","d[i,j]":"dist_min(i,j)_max(i,j)"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,8] for i in C"},"constraints":["For each i in C: sum(x[i,j] for j in V if j != i) = 1","For each j in C: sum(x[i,j] for i in V if i != j) = 1","sum(x[0,j] for j in C) = 2","sum(x[i,0] for i in C) = 2","For distinct i,j in C: u[i] - u[j] + 8*x[i,j] <= 7"],"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Find two nonempty depot-to-depot routes serving every clinic once."""
    nodes = tuple(range(9))
    clinics = tuple(range(1, 9))
    arcs = tuple(
        (i, j)
        for i in nodes
        for j in nodes
        if i != j
    )

    # Read all 36 supplied distances; use symmetry for reverse arcs.
    distances = {
        (i, j): params[f"dist_{i}_{j}"]
        for i in nodes
        for j in nodes
        if i < j
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.C = pyo.Set(initialize=clinics, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.d = pyo.Param(
        model.A,
        initialize={
            (i, j): distances[(min(i, j), max(i, j))]
            for i, j in arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.C, domain=pyo.Reals, bounds=(1, 8))

    def outgoing_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.V if j != i) == 1

    model.clinic_outgoing = pyo.Constraint(
        model.C, rule=outgoing_rule
    )

    def incoming_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.V if i != j) == 1

    model.clinic_incoming = pyo.Constraint(
        model.C, rule=incoming_rule
    )

    # Two departures and two returns represent the two identical vans.
    model.depot_departures = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.C) == 2
    )
    model.depot_returns = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in model.C) == 2
    )

    # Eliminate every cycle that does not contain the depot.
    def subtour_rule(mod, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return mod.u[i] - mod.u[j] + 8 * mod.x[i, j] <= 7

    model.subtour_elimination = pyo.Constraint(
        model.C, model.C, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.d[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}