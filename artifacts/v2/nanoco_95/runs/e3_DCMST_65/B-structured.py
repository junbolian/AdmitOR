# IR: {"sets":{"V":"0,...,n-1","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"n":"params['num_nodes']","c":"params['cost_matrix'], full row-major matrix (flat or nested)","d":"params['max_degree']"},"variables":{"x[i,j]":"binary, (i,j) in E","f[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["sum(x[i,j] for (i,j) in E) = n-1","sum(x[min(v,u),max(v,u)] for u in V if u!=v) <= d for v in V","f[i,j] <= (n-1)*x[min(i,j),max(i,j)] for (i,j) in A","sum(f[v,u]-f[u,v] for u in V if u!=v) = (n-1 if v==0 else -1) for v in V"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in E)"}

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = operator.index(params["num_nodes"])
    degree_limit = params["max_degree"]
    supplied_costs = list(params["cost_matrix"])

    if n < 1:
        raise ValueError("num_nodes must be a positive integer.")

    # Accept either the full flattened matrix or a nested square matrix.
    if len(supplied_costs) == n and all(
        hasattr(row, "__len__") for row in supplied_costs
    ):
        if any(len(row) != n for row in supplied_costs):
            raise ValueError("cost_matrix must have num_nodes columns per row.")
        flat_costs = [value for row in supplied_costs for value in row]
    else:
        flat_costs = supplied_costs

    if len(flat_costs) != n * n:
        raise ValueError("cost_matrix must contain num_nodes squared entries.")

    model = pyo.ConcreteModel()

    model.node_count = pyo.Param(initialize=n, within=pyo.PositiveIntegers)
    model.degree_limit = pyo.Param(
        initialize=degree_limit, within=pyo.NonNegativeReals
    )

    model.vertices = pyo.Set(initialize=range(n), ordered=True)
    model.edges = pyo.Set(
        dimen=2,
        initialize=[
            (i, j) for i in range(n) for j in range(i + 1, n)
        ],
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j) for i in range(n) for j in range(n) if i != j
        ],
    )

    model.track_cost = pyo.Param(
        model.vertices,
        model.vertices,
        initialize={
            (i, j): flat_costs[i * n + j]
            for i in range(n)
            for j in range(n)
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.edges, domain=pyo.Binary)
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Connectivity together with exactly n-1 undirected edges implies a tree.
    model.tree_edge_count = pyo.Constraint(
        expr=pyo.quicksum(model.x[i, j] for i, j in model.edges)
        == model.node_count - 1
    )

    def degree_rule(network, vertex):
        return pyo.quicksum(
            network.x[min(vertex, other), max(vertex, other)]
            for other in network.vertices
            if other != vertex
        ) <= network.degree_limit

    model.degree_bounds = pyo.Constraint(
        model.vertices, rule=degree_rule
    )

    def flow_capacity_rule(network, i, j):
        return network.f[i, j] <= (
            network.node_count - 1
        ) * network.x[min(i, j), max(i, j)]

    model.flow_capacity = pyo.Constraint(
        model.arcs, rule=flow_capacity_rule
    )

    # Root 0 supplies one flow unit to every other vertex.
    def flow_balance_rule(network, vertex):
        net_outflow = pyo.quicksum(
            network.f[vertex, other] - network.f[other, vertex]
            for other in network.vertices
            if other != vertex
        )
        required_outflow = (
            network.node_count - 1 if vertex == 0 else -1
        )
        return net_outflow == required_outflow

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=flow_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.track_cost[i, j] * model.x[i, j]
            for i, j in model.edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}