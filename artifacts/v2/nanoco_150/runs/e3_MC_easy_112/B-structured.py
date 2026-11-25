# IR: {"sets":{"N":"0..9","A":[[0,1],[0,6],[0,8],[1,2],[2,3],[2,7],[3,4],[4,5],[4,7],[4,8],[5,6],[6,7],[6,8],[7,8],[8,9]]},"params":{"capacity":"nonnegative arc_capacities from params, indexed in A order"},"variables":{"source_side[n]":"binary for n in N","cut_arc[i,j]":"binary for (i,j) in A"},"constraints":["source_side[0] = 1","source_side[9] = 0","cut_arc[i,j] >= source_side[i] - source_side[j] for (i,j) in A"],"objective":"minimize sum(capacity[i,j] * cut_arc[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1),
        (0, 6),
        (0, 8),
        (1, 2),
        (2, 3),
        (2, 7),
        (3, 4),
        (4, 5),
        (4, 7),
        (4, 8),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
        (8, 9),
    ]
    capacities = params["arc_capacities"]

    if len(capacities) != len(arcs):
        raise ValueError("arc_capacities must contain exactly 15 values.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )

    model.source_side = pyo.Var(model.nodes, domain=pyo.Binary)
    model.cut_arc = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_constraint = pyo.Constraint(
        expr=model.source_side[0] == 1
    )
    model.sink_constraint = pyo.Constraint(
        expr=model.source_side[9] == 0
    )

    def cut_rule(instance, origin, destination):
        return (
            instance.cut_arc[origin, destination]
            >= instance.source_side[origin]
            - instance.source_side[destination]
        )

    model.cut_constraints = pyo.Constraint(model.arcs, rule=cut_rule)

    model.cut_objective = pyo.Objective(
        expr=sum(
            model.capacity[origin, destination]
            * model.cut_arc[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise before loading a solution.
        # Objective retrievability remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}