import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    max_degree = params["max_degree"]

    num_nodes = len(distance_matrix)
    node_ids = list(range(num_nodes))
    edge_list = [(i, j) for i in node_ids for j in node_ids if i < j]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=node_ids)
    model.edges = pyo.Set(initialize=edge_list, dimen=2)

    model.x = pyo.Var(model.edges, within=pyo.Binary)

    def obj_rule(mdl):
        return sum(distance_matrix[i][j] * mdl.x[i, j] for (i, j) in edge_list)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Radial structure: exactly n-1 edges
    def edge_count_rule(mdl):
        return sum(mdl.x[i, j] for (i, j) in edge_list) == num_nodes - 1

    model.edge_count = pyo.Constraint(rule=edge_count_rule)

    # Degree upper bound
    def degree_rule(mdl, n):
        incident = []
        for (i, j) in edge_list:
            if i == n:
                incident.append(mdl.x[i, j])
            elif j == n:
                incident.append(mdl.x[i, j])
        return sum(incident) <= max_degree

    model.degree_limit = pyo.Constraint(model.nodes, rule=degree_rule)

    # Connectivity via single-commodity flow (root = node 0)
    root = 0
    big_m = num_nodes

    # Flow on directed arcs for each edge in both directions
    arcs = [(i, j) for (i, j) in edge_list] + [(j, i) for (i, j) in edge_list]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.f = pyo.Var(model.arcs, within=pyo.NonNegativeReals, bounds=(0, big_m))

    # Root sends n-1 units; every other node demands 1
    def flow_balance_rule(mdl, n):
        inflow = sum(mdl.f[i, n] for (i, j) in arcs if j == n)
        outflow = sum(mdl.f[n, j] for (i, j) in arcs if i == n)
        if n == root:
            return outflow - inflow == num_nodes - 1
        else:
            return inflow - outflow == 1

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    # Flow only along selected edges
    def flow_link_rule(mdl, i, j):
        if i < j:
            edge_var = mdl.x[i, j]
        else:
            edge_var = mdl.x[j, i]
        return mdl.f[i, j] <= big_m * edge_var

    model.flow_link = pyo.Constraint(model.arcs, rule=flow_link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}