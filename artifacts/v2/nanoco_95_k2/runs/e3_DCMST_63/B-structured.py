# IR: {"sets":{"V":"0..11","E":"(i,j) in VxV with i<j","A":"(i,j) in VxV with i!=j"},"params":{"pipe_cost_matrix":"12x12 symmetric costs, read from params","max_degree_per_node":"degree bound, read from params"},"variables":{"x[E]":"binary; installed undirected pipe","flow[A]":"nonnegative continuous; connectivity certificate"},"constraints":["sum(x[i,j] for (i,j) in E)=|V|-1","sum(x[i,j] for edges incident to v)<=max_degree_per_node for each v in V","sum(flow[v,j])-sum(flow[i,v])=|V|-1 if v=0, otherwise -1","flow[i,j]<=(|V|-1)*x[min(i,j),max(i,j)] for each (i,j) in A"],"objective":"minimize sum(pipe_cost_matrix[i][j]*x[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pipe_cost_matrix = params["pipe_cost_matrix"]
    max_degree_per_node = params["max_degree_per_node"]

    nodes = tuple(range(12))
    edges = tuple(
        (i, j) for i in nodes for j in nodes if i < j
    )
    arcs = tuple(
        (i, j) for i in nodes for j in nodes if i != j
    )
    flow_capacity = len(nodes) - 1

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.pipe_cost = pyo.Param(
        model.E,
        initialize={
            (i, j): pipe_cost_matrix[i][j] for i, j in edges
        },
        within=pyo.Reals,
    )
    model.degree_limit = pyo.Param(
        initialize=max_degree_per_node,
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    model.edge_count = pyo.Constraint(
        expr=sum(model.x[i, j] for i, j in edges) == len(nodes) - 1
    )

    def degree_rule(instance, v):
        return (
            sum(
                instance.x[i, j]
                for i, j in edges
                if i == v or j == v
            )
            <= instance.degree_limit
        )

    model.degree_bound = pyo.Constraint(model.V, rule=degree_rule)

    def flow_balance_rule(instance, v):
        outgoing = sum(
            instance.flow[v, j] for j in nodes if j != v
        )
        incoming = sum(
            instance.flow[i, v] for i in nodes if i != v
        )
        supply = flow_capacity if v == nodes[0] else -1
        return outgoing - incoming == supply

    model.flow_balance = pyo.Constraint(
        model.V, rule=flow_balance_rule
    )

    def flow_link_rule(instance, i, j):
        return (
            instance.flow[i, j]
            <= flow_capacity * instance.x[min(i, j), max(i, j)]
        )

    model.flow_link = pyo.Constraint(model.A, rule=flow_link_rule)

    # Connectivity plus exactly |V|-1 undirected edges ensures a tree.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.pipe_cost[i, j] * model.x[i, j]
            for i, j in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}