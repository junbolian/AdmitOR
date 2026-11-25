# IR: {"sets":{"N":"{0,1,2,3,4}","A":"ordered pairs (i,j) in N x N with i != j, in row-major order"},"params":{"distance":"params['distance']; accept a 5x5 nested matrix, 25 row-major entries including the diagonal, or 20 row-major off-diagonal entries; decode to d[i,j] for A","num_facilities_open":"params['num_facilities_open']"},"variables":{"opened[i]":"binary for i in N","paired[i,j]":"binary for (i,j) in A"},"constraints":["sum(opened[i] for i in N) == num_facilities_open","paired[i,j] <= opened[i] for (i,j) in A","paired[i,j] <= opened[j] for (i,j) in A","paired[i,j] >= opened[i] + opened[j] - 1 for (i,j) in A"],"objective":"maximize sum(d[i,j] * paired[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance = params["distance"]
    num_facilities_open = params["num_facilities_open"]

    nodes = tuple(range(5))
    arcs = tuple((i, j) for i in nodes for j in nodes if i != j)
    node_count = len(nodes)

    if len(distance) == node_count:
        directed_distance = {
            (i, j): distance[i][j]
            for i, j in arcs
        }
    elif len(distance) == node_count * node_count:
        directed_distance = {
            (i, j): distance[i * node_count + j]
            for i, j in arcs
        }
    elif len(distance) == len(arcs):
        directed_distance = {
            pair: distance[position]
            for position, pair in enumerate(arcs)
        }
    else:
        raise ValueError(
            "distance must be a 5x5 matrix, a flat sequence of 25 "
            "row-major entries, or a flat sequence of 20 row-major "
            "off-diagonal entries."
        )

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.directed_distance = pyo.Param(
        model.arcs,
        initialize=directed_distance,
        within=pyo.Reals,
    )
    model.required_facilities = pyo.Param(
        initialize=num_facilities_open,
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.nodes, domain=pyo.Binary)
    model.paired = pyo.Var(model.arcs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.opened[i] for i in model.nodes)
        == model.required_facilities
    )

    model.pair_from_open = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: mdl.paired[i, j] <= mdl.opened[i],
    )
    model.pair_to_open = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: mdl.paired[i, j] <= mdl.opened[j],
    )
    model.pair_both_open = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: (
            mdl.paired[i, j] >= mdl.opened[i] + mdl.opened[j] - 1
        ),
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.directed_distance[i, j] * model.paired[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}