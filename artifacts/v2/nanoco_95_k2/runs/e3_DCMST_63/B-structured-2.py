# IR: {"sets":{"V":"{0,...,11}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i,j in V, i!=j}"},"params":{"c[i,j]":"params['pipe_cost_matrix'][i][j] for (i,j) in E","D":"params['max_degree_per_node']","K":"|V|-1 (structural constant)"},"variables":{"x[i,j]":"Binary for (i,j) in E; install undirected pipe","f[i,j]":"NonNegativeReals for (i,j) in A; connectivity flow"},"constraints":["sum(x[i,j] for (i,j) in E) = K","sum(x[i,j] for (i,j) in E incident to v) <= D for v in V","sum(f[v,j] for j!=v) - sum(f[j,v] for j!=v) = K if v=0 else -1 for v in V","f[i,j] + f[j,i] <= K*x[i,j] for (i,j) in E"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the degree-constrained minimum-cost spanning-tree problem."""
    node_ids = tuple(range(12))
    edge_pairs = tuple(
        (i, j) for i in node_ids for j in node_ids if i < j
    )
    arc_pairs = tuple(
        (i, j) for i in node_ids for j in node_ids if i != j
    )

    pipe_cost_matrix = params["pipe_cost_matrix"]
    degree_limit = params["max_degree_per_node"]
    tree_edge_count = len(node_ids) - 1

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=node_ids, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edge_pairs, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arc_pairs, ordered=True)

    model.pipe_cost = pyo.Param(
        model.E,
        initialize={
            (i, j): pipe_cost_matrix[i][j] for i, j in edge_pairs
        },
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=degree_limit,
        within=pyo.Reals,
    )
    model.flow_requirement = pyo.Param(
        initialize=tree_edge_count,
        within=pyo.PositiveIntegers,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    model.edge_count_constraint = pyo.Constraint(
        expr=sum(model.x[i, j] for i, j in model.E)
        == model.flow_requirement
    )

    def degree_rule(current_model, vertex):
        return (
            sum(
                current_model.x[i, j]
                for i, j in current_model.E
                if i == vertex or j == vertex
            )
            <= current_model.degree_limit
        )

    model.degree_constraints = pyo.Constraint(
        model.V, rule=degree_rule
    )

    def flow_balance_rule(current_model, vertex):
        outgoing = sum(
            current_model.f[vertex, other]
            for other in current_model.V
            if other != vertex
        )
        incoming = sum(
            current_model.f[other, vertex]
            for other in current_model.V
            if other != vertex
        )
        required_balance = (
            current_model.flow_requirement if vertex == 0 else -1
        )
        return outgoing - incoming == required_balance

    model.flow_balance_constraints = pyo.Constraint(
        model.V, rule=flow_balance_rule
    )

    def flow_capacity_rule(current_model, i, j):
        return (
            current_model.f[i, j] + current_model.f[j, i]
            <= current_model.flow_requirement * current_model.x[i, j]
        )

    model.flow_capacity_constraints = pyo.Constraint(
        model.E, rule=flow_capacity_rule
    )

    # Connectivity plus exactly |V|-1 undirected edges implies a tree.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.pipe_cost[i, j] * model.x[i, j]
            for i, j in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when no solution can be loaded.
        # Propagate unrelated runtime errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}