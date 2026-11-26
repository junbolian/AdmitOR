# IR: {"sets":{"V":"range(n_nodes)","A":"{(i,j) in V x V: i != j}"},"params":{"n_nodes":"params['n_nodes']","source":"params['source']","sink":"params['sink']","cap":"params['cap'], indexed by (i,j), nonnegative"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in A","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= cap[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=source, -throughput if i=sink, otherwise 0"],"objective":"maximize throughput"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_nodes = params["n_nodes"]
    source = params["source"]
    sink = params["sink"]
    cap = params["cap"]

    if n_nodes < 2:
        return {"objective": None, "status": "invalid_node_count"}
    if source not in range(n_nodes) or sink not in range(n_nodes):
        return {"objective": None, "status": "invalid_terminal"}
    if source == sink:
        return {"objective": None, "status": "identical_terminals"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n_nodes - 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(n_nodes)
            for j in range(n_nodes)
            if i != j
        ),
    )

    def capacity_rule(mod, i, j):
        # Accept a mapping keyed by (i, j), or a nested matrix/mapping.
        if isinstance(cap, Mapping) and (i, j) in cap:
            return cap[(i, j)]
        return cap[i][j]

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_rule,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_limit_rule(mod, i, j):
        return mod.flow[i, j] <= mod.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_limit_rule
    )

    def balance_rule(mod, i):
        outgoing = pyo.quicksum(
            mod.flow[i, j] for j in mod.nodes if j != i
        )
        incoming = pyo.quicksum(
            mod.flow[j, i] for j in mod.nodes if j != i
        )
        if i == source:
            return outgoing - incoming == mod.throughput
        if i == sink:
            return outgoing - incoming == -mod.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.total_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_flow_objective))
    except (RuntimeError, ValueError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}