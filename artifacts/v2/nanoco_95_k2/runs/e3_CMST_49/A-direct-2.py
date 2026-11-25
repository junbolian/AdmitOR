import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost_matrix"]
    K = int(params["max_turbines_per_feeder"])
    n = int(params["num_nodes"])
    nt = int(params["num_turbines"])

    model = pyo.ConcreteModel()

    nodes = list(range(n))
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    model.NODES = pyo.Set(initialize=nodes)
    model.EDGES = pyo.Set(initialize=edges, dimen=2)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    # Directed flow variables for subtree sizes
    arcs = [(i, j) for (i, j) in edges] + [(j, i) for (i, j) in edges]
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.f = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.EDGES)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def tree_rule(m):
        return sum(m.x[i, j] for (i, j) in m.EDGES) == n - 1
    model.tree_con = pyo.Constraint(rule=tree_rule)

    # Map an arc (i,j) to the underlying undirected edge variable
    def edge_var(m, i, j):
        if i < j:
            return m.x[i, j]
        else:
            return m.x[j, i]

    # Flow bounded by chosen edge
    def flow_bound_rule(m, i, j):
        return m.f[i, j] <= (nt) * edge_var(m, i, j)
    model.flow_bound = pyo.Constraint(model.ARCS, rule=flow_bound_rule)

    # Flow conservation at turbine nodes: net inflow == 1 (node supplies itself)
    def flow_bal_rule(m, v):
        inflow = sum(m.f[i, v] for i in nodes if (i, v) in m.ARCS)
        outflow = sum(m.f[v, j] for j in nodes if (v, j) in m.ARCS)
        return inflow - outflow == 1
    model.flow_bal = pyo.Constraint(range(1, n), rule=flow_bal_rule)

    # Root balance: net outflow == nt
    def root_bal_rule(m):
        outflow = sum(m.f[0, j] for j in range(1, n))
        inflow = sum(m.f[i, 0] for i in range(1, n))
        return outflow - inflow == nt
    model.root_bal = pyo.Constraint(rule=root_bal_rule)

    # Feeder capacity: flow on each root edge <= K
    def feeder_cap_rule(m, j):
        return m.f[0, j] <= K
    model.feeder_cap = pyo.Constraint(range(1, n), rule=feeder_cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}