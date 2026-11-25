# IR: {"sets":{"V":"0..9","E":[[0,6],[0,8],[1,3],[1,6],[1,7],[1,9],[2,6],[2,8],[2,9],[3,7],[4,5],[4,7],[4,8],[4,9],[5,6],[5,9],[6,8]],"K":"0..16, indexing E in listed order"},"params":{"edge_weights":"real array indexed by K, read from params['edge_weights']","station_capacities":"real array indexed by V, read from params['station_capacities']"},"variables":{"x[k]":"binary for k in K"},"constraints":["For each v in V: sum(x[k] for k in K if v is an endpoint of E[k]) <= station_capacities[v]"],"objective":"maximize sum(edge_weights[k] * x[k] for k in K)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 6),
        (0, 8),
        (1, 3),
        (1, 6),
        (1, 7),
        (1, 9),
        (2, 6),
        (2, 8),
        (2, 9),
        (3, 7),
        (4, 5),
        (4, 7),
        (4, 8),
        (4, 9),
        (5, 6),
        (5, 9),
        (6, 8),
    )

    edge_weights = params["edge_weights"]
    station_capacities = params["station_capacities"]

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, 9)
    model.K = pyo.RangeSet(0, len(edges) - 1)

    model.edge_weights = pyo.Param(
        model.K,
        initialize=lambda mdl, k: edge_weights[k],
        within=pyo.Reals,
    )
    model.station_capacities = pyo.Param(
        model.V,
        initialize=lambda mdl, v: station_capacities[v],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.K, domain=pyo.Binary)

    def capacity_rule(mdl, v):
        return (
            sum(mdl.x[k] for k in mdl.K if v in edges[k])
            <= mdl.station_capacities[v]
        )

    model.capacity_constraints = pyo.Constraint(
        model.V,
        rule=capacity_rule,
    )

    model.total_score = pyo.Objective(
        expr=sum(model.edge_weights[k] * model.x[k] for k in model.K),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_score))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}