# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7],"links":[[0,1],[2,4],[2,7],[3,7],[1,4],[2,3],[0,5],[2,5],[3,5]]},"params":{"d[i]":"params['bandwidth_demand'][i], positive integer","H":"sum(d[i] for i in nodes)"},"variables":{"start[i]":"integer in [1,H-d[i]+1]","before[u,v]":"binary for each link","span":"integer in [1,H]"},"constraints":["Node i occupies the contiguous interval [start[i],start[i]+d[i]-1].","span >= start[i]+d[i]-1 for each node i.","start[u]+d[u] <= start[v]+H*(1-before[u,v]) for each link (u,v).","start[v]+d[v] <= start[u]+H*before[u,v] for each link (u,v)."],"objective":"minimize span"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(8), ordered=True)
    model.links = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1),
            (2, 4),
            (2, 7),
            (3, 7),
            (1, 4),
            (2, 3),
            (0, 5),
            (2, 5),
            (3, 5),
        ],
        ordered=True,
    )

    bandwidth_demand = params["bandwidth_demand"]
    model.demand = pyo.Param(
        model.nodes,
        initialize={
            node: bandwidth_demand[node]
            for node in model.nodes
        },
        within=pyo.PositiveIntegers,
    )
    model.horizon = pyo.Param(
        initialize=sum(
            pyo.value(model.demand[node])
            for node in model.nodes
        ),
        within=pyo.PositiveIntegers,
    )

    def start_bounds(problem, node):
        return (
            1,
            pyo.value(problem.horizon - problem.demand[node] + 1),
        )

    model.start = pyo.Var(
        model.nodes,
        domain=pyo.PositiveIntegers,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.links, domain=pyo.Binary)
    model.span = pyo.Var(
        domain=pyo.PositiveIntegers,
        bounds=(1, pyo.value(model.horizon)),
    )

    def span_rule(problem, node):
        return (
            problem.span
            >= problem.start[node] + problem.demand[node] - 1
        )

    model.span_limits = pyo.Constraint(
        model.nodes,
        rule=span_rule,
    )

    def forward_rule(problem, source, target):
        return (
            problem.start[source] + problem.demand[source]
            <= problem.start[target]
            + problem.horizon * (1 - problem.before[source, target])
        )

    model.forward_separation = pyo.Constraint(
        model.links,
        rule=forward_rule,
    )

    def reverse_rule(problem, source, target):
        return (
            problem.start[target] + problem.demand[target]
            <= problem.start[source]
            + problem.horizon * problem.before[source, target]
        )

    model.reverse_separation = pyo.Constraint(
        model.links,
        rule=reverse_rule,
    )

    model.spectrum_objective = pyo.Objective(
        expr=model.span,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.spectrum_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}