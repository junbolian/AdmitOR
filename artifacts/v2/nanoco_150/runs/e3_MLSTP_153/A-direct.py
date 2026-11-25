import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    nodes = list(range(num_nodes))

    candidate_edges = [tuple(e) for e in params["candidate_edges"]]
    leaf_reward = float(params["leaf_reward"])
    leaf_degree_target = int(params["leaf_degree_target"])

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=candidate_edges, dimen=2)

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    incident = {i: [] for i in nodes}
    for (i, j) in candidate_edges:
        incident[i].append((i, j))
        incident[j].append((i, j))

    # Degree of each node in the selected subgraph
    model.deg = pyo.Var(model.nodes, domain=pyo.NonNegativeReals,
                        bounds=(0, num_nodes))

    def deg_rule(model, i):
        return model.deg[i] == sum(model.x[e] for e in incident[i])

    model.deg_con = pyo.Constraint(model.nodes, rule=deg_rule)

    # Leaf indicator: 1 if deg == leaf_degree_target, else 0
    model.leaf = pyo.Var(model.nodes, domain=pyo.Binary)
    model.sel_lo = pyo.Var(model.nodes, domain=pyo.Binary)  # deg >= target
    model.sel_hi = pyo.Var(model.nodes, domain=pyo.Binary)  # deg <= target

    M = float(num_nodes)

    def sel_lo_rule(model, i):
        return model.deg[i] >= leaf_degree_target - M * (1 - model.sel_lo[i])

    def sel_hi_rule(model, i):
        return model.deg[i] <= leaf_degree_target + M * (1 - model.sel_hi[i])

    model.sel_lo_con = pyo.Constraint(model.nodes, rule=sel_lo_rule)
    model.sel_hi_con = pyo.Constraint(model.nodes, rule=sel_hi_rule)

    def leaf_link_con(model, i):
        return model.leaf[i] <= 0.5 * (model.sel_lo[i] + model.sel_hi[i])

    model.leaf_link = pyo.Constraint(model.nodes, rule=leaf_link_con)

    # Spanning tree: exactly N-1 edges
    def total_edges_rule(model):
        return sum(model.x[e] for e in candidate_edges) == num_nodes - 1

    model.total_edges = pyo.Constraint(rule=total_edges_rule)

    # Connectivity via flow from root 0
    flow = {}
    for e in candidate_edges:
        flow[e] = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, num_nodes))

    def flow_ub_rule(model, e):
        return flow[e] <= (num_nodes - 1) * model.x[e]

    model.flow_ub_con = pyo.Constraint(candidate_edges, rule=flow_ub_rule)

    def flow_balance(model, v):
        out_terms = []
        in_terms = []
        for e in candidate_edges:
            a, b = e
            if v == 0:
                if a == 0:
                    out_terms.append(flow[e])
                elif b == 0:
                    in_terms.append(flow[e])
            else:
                if a == v:
                    out_terms.append(flow[e])
                elif b == v:
                    in_terms.append(flow[e])
        if v == 0:
            return sum(out_terms) - sum(in_terms) == num_nodes - 1
        else:
            return sum(in_terms) - sum(out_terms) == 1

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance)

    model.obj_expr = sum(leaf_reward * model.leaf[i] for i in nodes)
    model.obj = pyo.Objective(expr=model.obj_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}