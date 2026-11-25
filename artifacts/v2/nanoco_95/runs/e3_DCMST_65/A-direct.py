import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]
    num_nodes = params["num_nodes"]

    nodes = list(range(num_nodes))
    edges = [(i, j) for i in nodes for j in nodes if i < j]

    # cost_matrix may be given as a flat list; index flattened row-major
    def edge_cost(i, j):
        return cost_matrix[i * num_nodes + j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(edge_cost(i, j) * model.x[i, j] for (i, j) in edges),
        sense=pyo.minimize,
    )

    # Exactly n-1 edges -> tree if connectivity enforced
    model.edge_count = pyo.Constraint(
        expr=sum(model.x[i, j] for (i, j) in edges) == num_nodes - 1
    )

    # Degree constraint at each node
    def degree_rule(mdl, v):
        return sum(
            mdl.x[i, j] for (i, j) in edges if i == v or j == v
        ) <= max_degree

    model.degree_con = pyo.Constraint(model.nodes, rule=degree_rule)

    # Connectivity via single-commodity flow from root
    root = nodes[0]
    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def flow_balance_rule(mdl, v):
        out_terms = sum(mdl.flow[i, j] for (i, j) in edges if i == v)
        in_terms = sum(mdl.flow[i, j] for (i, j) in edges if j == v)
        if v == root:
            return out_terms - in_terms == num_nodes - 1
        return in_terms - out_terms == 1

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def flow_cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= (num_nodes - 1) * mdl.x[i, j]

    model.flow_cap = pyo.Constraint(model.edges, rule=flow_cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}