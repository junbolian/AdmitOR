# IR: {"sets":{"V":[0,1,2,3,4,5],"E":[[0,3],[1,5],[2,4],[3,4]]},"params":{"d[0,3]":"params['weight_0_3']","d[1,5]":"params['weight_1_5']","d[2,4]":"params['weight_2_4']","d[3,4]":"params['weight_3_4']","U":"5*max(0,max(d[e] for e in E))","M[e]":"U+max(0,d[e])"},"variables":{"x[v]":"integer, 0<=x[v]<=U","span":"integer, 0<=span<=U","direction[e]":"binary"},"constraints":["x[v]<=span for v in V","x[u]-x[v]>=d[u,v]-M[u,v]*(1-direction[u,v]) for (u,v) in E","x[v]-x[u]>=d[u,v]-M[u,v]*direction[u,v] for (u,v) in E"],"objective":"minimize span"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(6))
    edges = ((0, 3), (1, 5), (2, 4), (3, 4))

    weights = {
        (0, 3): params["weight_0_3"],
        (1, 5): params["weight_1_5"],
        (2, 4): params["weight_2_4"],
        (3, 4): params["weight_3_4"],
    }

    # Assigning distinct multiples of the largest nonnegative weight
    # gives a feasible labeling within this bound.
    upper_bound = 5 * max(0, max(weights.values()))
    big_m = {
        edge: upper_bound + max(0, weights[edge])
        for edge in edges
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)

    model.separation = pyo.Param(model.edges, initialize=weights)
    model.disjunction_bound = pyo.Param(model.edges, initialize=big_m)

    model.platform_index = pyo.Var(
        model.vertices,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.span = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.direction = pyo.Var(model.edges, domain=pyo.Binary)

    def span_rule(instance, vertex):
        return instance.platform_index[vertex] <= instance.span

    model.span_limits = pyo.Constraint(model.vertices, rule=span_rule)

    def forward_rule(instance, source, target):
        return (
            instance.platform_index[source]
            - instance.platform_index[target]
            >= instance.separation[source, target]
            - instance.disjunction_bound[source, target]
            * (1 - instance.direction[source, target])
        )

    model.forward_separation = pyo.Constraint(
        model.edges, rule=forward_rule
    )

    def reverse_rule(instance, source, target):
        return (
            instance.platform_index[target]
            - instance.platform_index[source]
            >= instance.separation[source, target]
            - instance.disjunction_bound[source, target]
            * instance.direction[source, target]
        )

    model.reverse_separation = pyo.Constraint(
        model.edges, rule=reverse_rule
    )

    model.total_span = pyo.Objective(
        expr=model.span,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_span))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}