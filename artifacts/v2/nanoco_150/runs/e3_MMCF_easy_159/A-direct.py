import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    demand = params["demand"]

    # Structural constants: 30 directed arcs in the given order
    arcs = [
        (0, 1), (1, 0), (0, 4), (4, 0),
        (1, 2), (2, 1), (1, 3), (3, 1),
        (1, 5), (5, 1), (1, 6), (6, 1),
        (2, 3), (3, 2), (3, 4), (4, 3),
        (4, 5), (5, 4), (5, 6), (6, 5),
        (5, 9), (9, 5), (6, 7), (7, 6),
        (7, 8), (8, 7), (7, 9), (9, 7),
        (8, 9), (9, 8),
    ]
    arc_idx = list(range(len(arcs)))

    # Requests: (origin, destination, demand value)
    requests = [
        (1, 4, demand[0]),
        (7, 9, demand[1]),
    ]
    req_idx = list(range(len(requests)))

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arc_idx)
    model.REQS = pyo.Set(initialize=req_idx)

    # Flow of each request on each directed arc (nonnegative)
    model.flow = pyo.Var(model.REQS, model.ARCS, domain=pyo.NonNegativeReals)

    # Maximum utilization variable
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    # Flow balance constraints per request at each node
    nodes = list(range(10))
    model.NODES = pyo.Set(initialize=nodes)

    def balance_rule(m, k, n):
        origin, dest, dem = requests[k]
        if n == origin:
            return sum(m.flow[k, a] for a in arc_idx if arcs[a][0] == n) \
                   - sum(m.flow[k, a] for a in arc_idx if arcs[a][1] == n) == dem
        elif n == dest:
            return sum(m.flow[k, a] for a in arc_idx if arcs[a][0] == n) \
                   - sum(m.flow[k, a] for a in arc_idx if arcs[a][1] == n) == -dem
        else:
            return sum(m.flow[k, a] for a in arc_idx if arcs[a][0] == n) \
                   - sum(m.flow[k, a] for a in arc_idx if arcs[a][1] == n) == 0

    model.balance = pyo.Constraint(model.REQS, model.NODES, rule=balance_rule)

    # Aggregate flow on each arc must not exceed capacity
    def cap_rule(m, a):
        return sum(m.flow[k, a] for k in req_idx) <= arc_capacity[a]

    model.capacity = pyo.Constraint(model.ARCS, rule=cap_rule)

    # Utilization: aggregate flow / capacity <= z
    def util_rule(m, a):
        return sum(m.flow[k, a] for k in req_idx) <= arc_capacity[a] * m.z

    model.utilization = pyo.Constraint(model.ARCS, rule=util_rule)

    # Objective: minimize maximum utilization
    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}