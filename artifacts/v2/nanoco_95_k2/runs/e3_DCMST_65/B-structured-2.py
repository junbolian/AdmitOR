# IR: {"sets":{"V":"{0,...,14}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"cost_matrix":"params['cost_matrix'], symmetric 15x15 construction costs","max_degree":"params['max_degree']"},"variables":{"x[i,j]":"Binary for (i,j) in E","flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each v in V: sum(x[i,j] for (i,j) in E incident to v) <= max_degree","sum(x[i,j] for (i,j) in E) = |V|-1","For each (i,j) in A: flow[i,j] <= (|V|-1)*x[min(i,j),max(i,j)]","For each v in V: sum(flow[v,j] for j!=v)-sum(flow[j,v] for j!=v) = |V|-1 if v=0 else -1"],"objective":"Minimize sum(cost_matrix[i][j]*x[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]

    nodes = tuple(range(15))
    edges = tuple(
        (i, j) for i in nodes for j in nodes if i < j
    )
    arcs = tuple(
        (i, j) for i in nodes for j in nodes if i != j
    )
    root = nodes[0]
    required_edges = len(nodes) - 1

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.edge_cost = pyo.Param(
        model.E,
        initialize={
            (i, j): cost_matrix[i][j] for i, j in edges
        },
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=max_degree,
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def degree_rule(network, v):
        return (
            sum(
                network.x[i, j]
                for i, j in edges
                if i == v or j == v
            )
            <= network.degree_limit
        )

    model.degree_constraints = pyo.Constraint(
        model.V, rule=degree_rule
    )

    model.tree_edge_count = pyo.Constraint(
        expr=sum(model.x[i, j] for i, j in edges)
        == required_edges
    )

    def capacity_rule(network, i, j):
        return (
            network.flow[i, j]
            <= required_edges * network.x[min(i, j), max(i, j)]
        )

    model.flow_capacity = pyo.Constraint(
        model.A, rule=capacity_rule
    )

    def balance_rule(network, v):
        outgoing = sum(
            network.flow[v, j] for j in nodes if j != v
        )
        incoming = sum(
            network.flow[j, v] for j in nodes if j != v
        )
        supply = required_edges if v == root else -1
        return outgoing - incoming == supply

    model.flow_balance = pyo.Constraint(
        model.V, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.edge_cost[i, j] * model.x[i, j]
            for i, j in edges
        ),
        sense=pyo.minimize,
    )

    # APPsi HiGHS raises RuntimeError when it cannot load a solution.
    # Objective retrieval below is the sole success test.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}