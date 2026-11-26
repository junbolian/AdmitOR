# IR: {"sets":{"N":"range(params['num_centers'])","A":"{(i,j) in N x N: i != j}","T":"N excluding source and sink"},"params":{"n":"params['num_centers']","s":"params['source_node']","t":"params['sink_node']","c":"params['capacity_matrix']; each row may contain n entries or n-1 entries omitting its diagonal; diagonal capacity is zero"},"variables":{"f[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["f[i,j] <= c[i,j] for (i,j) in A","sum_j f[v,j] == sum_i f[i,v] for v in T"],"objective":"maximize sum_j f[s,j] - sum_i f[i,s]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["num_centers"]
    source = params["source_node"]
    sink = params["sink_node"]
    capacity_matrix = params["capacity_matrix"]

    if (
        not isinstance(n, int)
        or isinstance(n, bool)
        or n < 2
        or not isinstance(source, int)
        or isinstance(source, bool)
        or not isinstance(sink, int)
        or isinstance(sink, bool)
        or source not in range(n)
        or sink not in range(n)
        or source == sink
        or len(capacity_matrix) != n
    ):
        return {"objective": None, "status": "invalid_parameters"}

    capacities = {}
    for i in range(n):
        row = capacity_matrix[i]
        if len(row) not in (n, n - 1):
            return {"objective": None, "status": "invalid_capacity_shape"}

        for j in range(n):
            if i == j:
                continue

            column = j if len(row) == n or j < i else j - 1
            capacity = float(row[column])
            if not math.isfinite(capacity) or capacity < 0:
                return {"objective": None, "status": "invalid_capacity"}
            capacities[i, j] = capacity

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(n), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j],
        ordered=True,
    )
    model.transit_nodes = pyo.Set(
        initialize=[v for v in range(n) if v != source and v != sink],
        ordered=True,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity[i, j]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(mdl, v):
        outgoing = sum(mdl.flow[v, j] for j in mdl.nodes if j != v)
        incoming = sum(mdl.flow[i, v] for i in mdl.nodes if i != v)
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes,
        rule=conservation_rule,
    )
    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[source, j] for j in model.nodes if j != source)
            - sum(model.flow[i, source] for i in model.nodes if i != source)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}