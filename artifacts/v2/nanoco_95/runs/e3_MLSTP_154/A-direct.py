import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    edges = [
        (3, 7), (1, 6), (0, 8), (1, 9), (2, 8), (4, 5), (5, 9),
        (4, 11), (9, 10), (0, 10), (2, 7), (1, 5), (1, 11), (4, 7),
        (3, 8), (5, 11), (8, 10), (0, 9), (0, 6), (2, 3), (6, 9)
    ]
    edge_weights = params["edge_weights"]

    n_nodes = 12
    nodes = list(range(n_nodes))
    edge_list = [tuple(e) for e in edges]
    n_edges = len(edge_list)

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes)
    model.E = pyo.Set(initialize=list(range(n_edges)))

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.deg = pyo.Var(model.V, domain=pyo.NonNegativeReals, bounds=(0, n_nodes - 1))
    model.is_leaf = pyo.Var(model.V, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.is_leaf[v] for v in model.V), sense=pyo.maximize)

    # Degree definitions
    def deg_rule(m, v):
        return m.deg[v] == sum(m.x[e] for e in m.E
                               if edge_list[e][0] == v or edge_list[e][1] == v)
    model.deg_con = pyo.Constraint(model.V, rule=deg_rule)

    # Leaf linking: is_leaf[v] <= 1 and is_leaf[v] <= 2 - deg[v]
    def leaf_link_1(m, v):
        return m.is_leaf[v] <= 1
    model.leaf_link1 = pyo.Constraint(model.V, rule=leaf_link_1)

    def leaf_link_2(m, v):
        return m.is_leaf[v] <= 2 - m.deg[v]
    model.leaf_link2 = pyo.Constraint(model.V, rule=leaf_link_2)

    # Spanning tree: exactly n-1 edges
    model.edge_count = pyo.Constraint(expr=sum(model.x[e] for e in model.E) == n_nodes - 1)

    # Connectivity via single-commodity flow from root 0 (with orientation per edge artificially chosen as listed)
    # Use directed flow variables along both directions handled by assignment per edge's canonical orientation.
    model.f = pyo.Var(model.E, domain=pyo.NonNegativeReals)
    model.flow_balance = pyo.ConstraintList()
    for v in model.V:
        inflow = sum(model.f[e] for e in model.E if edge_list[e][1] == v)
        outflow = sum(model.f[e] for e in model.E if edge_list[e][0] == v)
        if v == 0:
            model.flow_balance.add(outflow - inflow == n_nodes - 1)
        else:
            model.flow_balance.add(inflow - outflow == 1)

    def flow_cap(m, e):
        return m.f[e] <= (n_nodes - 1) * m.x[e]
    model.flow_cap = pyo.Constraint(model.E, rule=flow_cap)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}