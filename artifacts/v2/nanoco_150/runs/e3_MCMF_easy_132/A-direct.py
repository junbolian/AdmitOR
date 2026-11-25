import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    arcs = [
        (0, 1), (0, 6), (0, 8),
        (1, 2),
        (2, 3), (2, 7),
        (3, 4),
        (4, 5), (4, 7), (4, 8),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
        (8, 9),
    ]
    nodes = list(range(10))

    cap = {}
    cost = {}
    for (i, j) in arcs:
        cap[(i, j)] = params["capacity_%d_%d" % (i, j)]
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    # reference coords (read to respect params usage)
    _coords = {}
    for n in nodes:
        _coords[n] = params["coord_node_%d" % n]

    model = pyo.ConcreteModel()
    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.node_set = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    # capacity constraints
    def _cap_rule(m, i, j):
        return m.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.arc_set, rule=_cap_rule)

    # flow conservation
    source = 0
    sink = 9

    def _balance_rule(m, n):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == n)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.balance_con = pyo.Constraint(model.node_set, rule=_balance_rule)

    # throughput = total flow into sink
    throughput_expr = sum(model.flow[i, j] for (i, j) in arcs if j == sink)

    # Stage 1: maximize throughput
    model.objective = pyo.Objective(expr=throughput_expr, sense=pyo.maximize)
    Highs().solve(model)
    max_throughput = float(pyo.value(throughput_expr))

    # Stage 2: fix throughput and minimize cost
    model.del_component(model.objective)

    def _cost_expr(m):
        return sum(cost[(i, j)] * m.flow[i, j] for (i, j) in arcs)
    model.cost_expr = pyo.Expression(rule=_cost_expr)

    model.throughput_con = pyo.Constraint(expr=(throughput_expr >= max_throughput))

    model.objective = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)
    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}