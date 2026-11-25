# IR: {"sets":{"V":"{0,...,8}","C":"{1,...,8}","A":"{(i,j) in V x V: i != j}","E":"{(i,j) in V x V: i < j}"},"params":{"d[i,j]":"params['dist_i_j'] for (i,j) in E; d[j,i]=d[i,j]"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous in [1,8], i in C"},"constraints":["sum(j in V, j != i) x[i,j] = 1 for i in C","sum(j in V, j != i) x[j,i] = 1 for i in C","sum(j in C) x[0,j] = 2","sum(i in C) x[i,0] = 2","u[i]-u[j]+8*x[i,j] <= 7 for distinct i,j in C"],"objective":"minimize sum((i,j) in A) d[i,j]*x[i,j]"}
#
# Two depot departures and returns represent the two identical vans.
# The ordering constraints eliminate all cycles that exclude the depot.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(9))
    clinics = tuple(range(1, 9))
    arcs = tuple(
        (i, j)
        for i in nodes
        for j in nodes
        if i != j
    )
    clinic_count = len(clinics)

    pair_distances = {
        (i, j): params[f"dist_{i}_{j}"]
        for i in nodes
        for j in nodes
        if i < j
    }
    arc_distances = {
        (i, j): pair_distances[(min(i, j), max(i, j))]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=nodes, ordered=True)
    model.clinic_set = pyo.Set(initialize=clinics, ordered=True)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.distance = pyo.Param(
        model.arc_set,
        initialize=arc_distances,
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arc_set, domain=pyo.Binary)
    model.u = pyo.Var(
        model.clinic_set,
        domain=pyo.Reals,
        bounds=(1, clinic_count),
    )

    def clinic_departure_rule(instance, i):
        return sum(
            instance.x[i, j]
            for j in nodes
            if j != i
        ) == 1

    model.clinic_departure = pyo.Constraint(
        model.clinic_set,
        rule=clinic_departure_rule,
    )

    def clinic_arrival_rule(instance, i):
        return sum(
            instance.x[j, i]
            for j in nodes
            if j != i
        ) == 1

    model.clinic_arrival = pyo.Constraint(
        model.clinic_set,
        rule=clinic_arrival_rule,
    )

    model.depot_departures = pyo.Constraint(
        expr=sum(model.x[0, j] for j in clinics) == 2
    )
    model.depot_returns = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in clinics) == 2
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i]
            - instance.u[j]
            + clinic_count * instance.x[i, j]
            <= clinic_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.clinic_set,
        model.clinic_set,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}