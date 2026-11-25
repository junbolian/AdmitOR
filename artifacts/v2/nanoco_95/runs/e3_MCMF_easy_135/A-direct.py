import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # ---- structural constants ----
    num_nodes = int(params["num_nodes"])
    N = range(num_nodes)
    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]
    source = 0
    sink = num_nodes - 1

    cap = {(i, j): params["capacity_%d_%d" % (i, j)] for (i, j) in arcs}
    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    # ---- model ----
    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=arcs, dimen=2)
    model.V = pyo.Set(initialize=list(N))

    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    # throughput: net flow out of source
    def throughput_rule(model):
        return sum(model.f[i, j] for (i, j) in arcs if i == source) \
             - sum(model.f[i, j] for (i, j) in arcs if j == source)
    model.throughput = pyo.Expression(rule=throughput_rule)

    def cost_rule(model):
        return sum(cost[i, j] * model.f[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Expression(rule=cost_rule)

    # capacity
    def cap_rule(model, i, j):
        return model.f[i, j] <= cap[i, j]
    model.cap_con = pyo.Constraint(model.A, rule=cap_rule)

    # flow conservation at intermediate nodes (and sink/source handled)
    def flow_rule(model, k):
        if k == source or k == sink:
            return pyo.Constraint.Skip
        inflow = sum(model.f[i, j] for (i, j) in arcs if j == k)
        outflow = sum(model.f[i, j] for (i, j) in arcs if i == k)
        return inflow - outflow == 0
    model.flow_con = pyo.Constraint(model.V, rule=flow_rule)

    # ---- stage 1: maximize throughput ----
    model.obj1 = pyo.Objective(expr=model.throughput, sense=pyo.maximize)
    Highs().solve(model)
    max_throughput = pyo.value(model.throughput)

    # ---- stage 2: fix throughput, minimize cost ----
    model.throughput_fix = pyo.Constraint(
        expr=model.throughput >= max_throughput - 1e-6)
    model.del_component(model.obj1)
    model.obj2 = pyo.Objective(expr=model.total_cost, sense=pyo.minimize)
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}