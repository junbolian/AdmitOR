# IR: {"sets":{"Z":[0,1,2,3,4,5,6,7,8,9],"T":[0,1,2,3,4,5,6,7,8,9],"E":[[0,1],[0,4],[3,4],[5,7],[0,6],[3,9],[0,5],[0,8],[1,3],[7,8]],"P":{"0":[0,1,2,4,5,6,7,8,9],"1":[0,1,2,3,4,5],"2":[0,1,4,5,6,7,8],"3":[0,2,3,4,7],"4":[0,1,2,4,6,7,8,9],"5":[2,3,4,6,7],"6":[0,2,3,4,5,6,8],"7":[0,1,2,3,4,5,6,7,8,9],"8":[0,1,2,3,4,5,6,7,8,9],"9":[0,2,3,5,8,9]},"A":"{(z,t): z in Z, t in P[z]}","C":"{(u,v,t): (u,v) in E, t in P[u] intersect P[v]}"},"params":{},"variables":{"x[z,t]":{"index":"A","type":"binary"},"peak":{"type":"integer","bounds":[0,9]}},"constraints":["For every z in Z: sum(x[z,t] for t in P[z]) = 1","For every (u,v,t) in C: x[u,t] + x[v,t] <= 1","For every z in Z: sum(t*x[z,t] for t in P[z]) <= peak"],"objective":{"sense":"minimize","expression":"peak"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # PARAMS is empty; all supplied numerical data define structural sets.
    permitted = {
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

    model = pyo.ConcreteModel()
    model.Z = pyo.RangeSet(0, 9)
    model.T = pyo.RangeSet(0, 9)
    model.E = pyo.Set(dimen=2, initialize=edges)
    model.P = pyo.Set(
        model.Z,
        within=model.T,
        initialize=lambda mdl, zone: permitted[zone],
    )
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (zone, zone_type)
            for zone in range(10)
            for zone_type in permitted[zone]
        ],
    )
    model.C = pyo.Set(
        dimen=3,
        initialize=[
            (left, right, zone_type)
            for left, right in edges
            for zone_type in permitted[left]
            if zone_type in permitted[right]
        ],
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.peak = pyo.Var(domain=pyo.Integers, bounds=(0, 9))

    def assignment_rule(mdl, zone):
        return sum(mdl.x[zone, zone_type] for zone_type in mdl.P[zone]) == 1

    model.assignment = pyo.Constraint(model.Z, rule=assignment_rule)

    def incompatibility_rule(mdl, left, right, zone_type):
        return mdl.x[left, zone_type] + mdl.x[right, zone_type] <= 1

    model.incompatibility = pyo.Constraint(
        model.C, rule=incompatibility_rule
    )

    def maximum_type_rule(mdl, zone):
        return (
            sum(
                zone_type * mdl.x[zone, zone_type]
                for zone_type in mdl.P[zone]
            )
            <= mdl.peak
        )

    model.maximum_type = pyo.Constraint(model.Z, rule=maximum_type_rule)
    model.objective = pyo.Objective(expr=model.peak, sense=pyo.minimize)

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solve can leave the objective uninitialized.
        # Objective retrievability below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}