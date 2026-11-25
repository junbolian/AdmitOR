# IR: {"sets":{"zones":[0,1,2,3,4,5,6,7,8,9],"types":[0,1,2,3,4,5,6,7,8,9],"edges":[[0,1],[0,4],[3,4],[5,7],[0,6],[3,9],[0,5],[0,8],[1,3],[7,8]],"allowed":{"0":[0,1,2,4,5,6,7,8,9],"1":[0,1,2,3,4,5],"2":[0,1,4,5,6,7,8],"3":[0,2,3,4,7],"4":[0,1,2,4,6,7,8,9],"5":[2,3,4,6,7],"6":[0,2,3,4,5,6,8],"7":[0,1,2,3,4,5,6,7,8,9],"8":[0,1,2,3,4,5,6,7,8,9],"9":[0,2,3,5,8,9]}},"params":{},"variables":{"x[i,k]":"binary for i in zones and k in allowed[i]","z":"nonnegative integer"},"constraints":["sum(x[i,k] for k in allowed[i]) == 1 for each zone i","x[i,k] + x[j,k] <= 1 for each edge (i,j) and each k in allowed[i] intersect allowed[j]","sum(k*x[i,k] for k in allowed[i]) <= z for each zone i"],"objective":"minimize z"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # PARAMS is empty; all instance data below defines the index structure.
    zones = tuple(range(10))
    types = tuple(range(10))

    edges = (
        (0, 1),
        (0, 4),
        (3, 4),
        (5, 7),
        (0, 6),
        (3, 9),
        (0, 5),
        (0, 8),
        (1, 3),
        (7, 8),
    )

    allowed = {
        0: (0, 1, 2, 4, 5, 6, 7, 8, 9),
        1: (0, 1, 2, 3, 4, 5),
        2: (0, 1, 4, 5, 6, 7, 8),
        3: (0, 2, 3, 4, 7),
        4: (0, 1, 2, 4, 6, 7, 8, 9),
        5: (2, 3, 4, 6, 7),
        6: (0, 2, 3, 4, 5, 6, 8),
        7: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
        8: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
        9: (0, 2, 3, 5, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.zones = pyo.Set(initialize=zones, ordered=True)
    model.types = pyo.Set(initialize=types, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges)
    model.allowed_types = pyo.Set(
        model.zones,
        within=model.types,
        initialize=lambda mdl, i: allowed[i],
    )
    model.assignment_pairs = pyo.Set(
        dimen=2,
        initialize=((i, k) for i in zones for k in allowed[i]),
    )
    model.conflict_triples = pyo.Set(
        dimen=3,
        initialize=(
            (i, j, k)
            for i, j in edges
            for k in allowed[i]
            if k in allowed[j]
        ),
    )

    model.x = pyo.Var(model.assignment_pairs, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeIntegers)

    def assignment_rule(mdl, i):
        return sum(mdl.x[i, k] for k in mdl.allowed_types[i]) == 1

    model.assignment_constraints = pyo.Constraint(
        model.zones, rule=assignment_rule
    )

    def incompatibility_rule(mdl, i, j, k):
        return mdl.x[i, k] + mdl.x[j, k] <= 1

    model.incompatibility_constraints = pyo.Constraint(
        model.conflict_triples, rule=incompatibility_rule
    )

    def maximum_type_rule(mdl, i):
        return (
            sum(k * mdl.x[i, k] for k in mdl.allowed_types[i])
            <= mdl.z
        )

    model.maximum_type_constraints = pyo.Constraint(
        model.zones, rule=maximum_type_rule
    )

    model.objective = pyo.Objective(expr=model.z, sense=pyo.minimize)

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Let unrelated runtime errors propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}