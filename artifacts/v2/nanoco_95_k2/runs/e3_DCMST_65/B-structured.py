# IR: {"sets":{"V":"{1,...,15}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"cost_matrix":"params['cost_matrix'], indexed by [i-1][j-1]","max_degree":"params['max_degree']"},"variables":{"x[i,j]":"Binary for (i,j) in E","flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["sum(x[i,j] for (i,j) in E) = |V|-1","For each v in V: sum(x[i,j] for (i,j) in E if v in {i,j}) <= max_degree","For each (i,j) in A: flow[i,j] <= (|V|-1)*x[min(i,j),max(i,j)]","For each v in V: sum(flow[v,j] for j in V\\{v}) - sum(flow[j,v] for j in V\\{v}) = |V|-1 if v=1, else -1"],"objective":"Minimize sum(cost_matrix[i-1][j-1]*x[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]

    nodes = list(range(1, 16))
    edges = [
        (source, target)
        for source in nodes
        for target in nodes
        if source < target
    ]
    arcs = [
        (source, target)
        for source in nodes
        for target in nodes
        if source != target
    ]
    root = nodes[0]
    required_edges = len(nodes) - 1

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.edge_cost = pyo.Param(
        model.E,
        initialize={
            (source, target): cost_matrix[source - 1][target - 1]
            for source, target in edges
        },
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=max_degree,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    model.tree_edge_count = pyo.Constraint(
        expr=sum(model.x[source, target] for source, target in edges)
        == required_edges
    )

    def degree_rule(network, node):
        return (
            sum(
                network.x[source, target]
                for source, target in edges
                if source == node or target == node
            )
            <= network.degree_limit
        )

    model.degree_constraints = pyo.Constraint(
        model.V,
        rule=degree_rule,
    )

    def capacity_rule(network, source, target):
        edge = (min(source, target), max(source, target))
        return (
            network.flow[source, target]
            <= required_edges * network.x[edge]
        )

    model.flow_capacity = pyo.Constraint(
        model.A,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        outgoing = sum(
            network.flow[node, other]
            for other in nodes
            if other != node
        )
        incoming = sum(
            network.flow[other, node]
            for other in nodes
            if other != node
        )
        supply = required_edges if node == root else -1
        return outgoing - incoming == supply

    model.flow_balance = pyo.Constraint(
        model.V,
        rule=balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.edge_cost[source, target] * model.x[source, target]
            for source, target in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "feasible solution" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}