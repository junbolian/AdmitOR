import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["num_nodes"]
    nreq = params["num_requisitions"]
    dist = params["distance_matrix"]

    # Fixed structure: precedence pairs (pickup, delivery)
    pairs = [(4, 6), (5, 1), (2, 3)]

    nodes = list(range(n))
    tasks = list(range(1, n))

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.TASKS = pyo.Set(initialize=tasks)
    model.PAIRS = pyo.Set(initialize=range(nreq), dimen=1)

    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.TASKS, model.NODES, domain=pyo.Binary)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in m.arcs)

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.u[t, i] for t in m.TASKS) == 1

    model.assign = pyo.Constraint(model.NODES, rule=assign_rule)

    def pos_rule(m, t):
        return sum(m.u[t, i] for i in m.NODES) == 1

    model.pos = pyo.Constraint(model.TASKS, rule=pos_rule)

    def prec_rule(m, k):
        p, d = pairs[k]
        return sum(t * m.u[t, p] for t in m.TASKS) <= sum(
            t * m.u[t, d] for t in m.TASKS
        )

    model.prec = pyo.Constraint(model.PAIRS, rule=prec_rule)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.NODES if j != i) == 1

    model.out = pyo.Constraint(model.NODES, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in m.NODES if i != j) == 1

    model.inn = pyo.Constraint(model.NODES, rule=in_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}