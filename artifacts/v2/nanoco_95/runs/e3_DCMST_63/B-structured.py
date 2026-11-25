# IR: {"sets":{"V":"0..11","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"costs":"symmetric 12x12 matrix from params['costs']","max_degree":"maximum node degree from params['max_degree']"},"variables":{"selected[E]":"binary","flow[A]":"nonnegative continuous"},"constraints":["sum(selected[i,j] for (i,j) in E) = |V|-1","for each v in V: sum(selected[i,j] for incident (i,j) in E) <= max_degree","for each (i,j) in A: flow[i,j] <= (|V|-1)*selected[min(i,j),max(i,j)]","for each v in V: outgoing_flow(v)-incoming_flow(v) = |V|-1 if v=0 else -1"],"objective":"minimize sum(costs[i][j]*selected[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(12))
    edges = tuple(
        (i, j) for i in nodes for j in nodes if i < j
    )
    arcs = tuple(
        (i, j) for i in nodes for j in nodes if i != j
    )
    node_count = len(nodes)

    input_costs = params["costs"]
    input_max_degree = params["max_degree"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.pipe_cost = pyo.Param(
        model.edges,
        initialize={(i, j): input_costs[i][j] for i, j in edges},
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=input_max_degree,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.edges, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.edge_count_constraint = pyo.Constraint(
        expr=sum(model.selected[i, j] for i, j in model.edges)
        == node_count - 1
    )

    def degree_rule(instance, vertex):
        return (
            sum(
                instance.selected[i, j]
                for i, j in instance.edges
                if i == vertex or j == vertex
            )
            <= instance.degree_limit
        )

    model.degree_constraints = pyo.Constraint(
        model.nodes, rule=degree_rule
    )

    def capacity_rule(instance, i, j):
        return (
            instance.flow[i, j]
            <= (node_count - 1)
            * instance.selected[min(i, j), max(i, j)]
        )

    model.flow_capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(instance, vertex):
        outgoing = sum(
            instance.flow[vertex, other]
            for other in instance.nodes
            if other != vertex
        )
        incoming = sum(
            instance.flow[other, vertex]
            for other in instance.nodes
            if other != vertex
        )
        supply = node_count - 1 if vertex == 0 else -1
        return outgoing - incoming == supply

    model.flow_balance_constraints = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.pipe_cost[i, j] * model.selected[i, j]
            for i, j in model.edges
        ),
        sense=pyo.minimize,
    )

    # Connectivity plus exactly |V|-1 undirected edges implies a tree.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}