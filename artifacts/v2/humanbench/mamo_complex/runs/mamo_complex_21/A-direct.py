import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 9
    source = 0
    sink = 8

    # Build capacity dict from params
    cap = {}
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            name = "capacity_{}_{}".format(i, j)
            if name in params:
                cap[(i, j)] = params[name]
            else:
                cap[(i, j)] = 0.0

    # max_capacity_from_k applies to all outgoing links from k (except where explicit? apply as bound)
    for k in range(N):
        key = "max_capacity_from_{}".format(k)
        if key in params:
            ub = params[key]
            for j in range(N):
                if j != k:
                    if (k, j) in cap and cap[(k, j)] > ub:
                        cap[(k, j)] = ub
    # max_capacity_to_k applies to all incoming links into k
    for k in range(N):
        key = "max_capacity_to_{}".format(k)
        if key in params:
            ub = params[key]
            for i in range(N):
                if i != k:
                    if (i, k) in cap and cap[(i, k)] > ub:
                        cap[(i, k)] = ub

    arcs = [(i, j) for i in range(N) for j in range(N) if i != j and cap[(i, j)] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Conservation
    def balance_rule(m, n):
        inflow = sum(m.flow[i, n] for (i, j) in arcs if j == n)
        outflow = sum(m.flow[n, j] for (i, j) in arcs if i == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.balance = pyo.Constraint(range(N), rule=balance_rule)

    # Capacity
    def cap_rule(m, i, j):
        return m.flow[i, j] <= cap[(i, j)]
    model.capcon = pyo.Constraint(model.arcs, rule=cap_rule)

    # Objective: maximize net outflow from source
    def obj_rule(m):
        return sum(m.flow[source, j] for (i, j) in arcs if i == source)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}