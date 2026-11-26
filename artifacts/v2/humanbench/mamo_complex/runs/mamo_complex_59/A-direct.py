import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 9
    source = 0
    sink = 8

    model = pyo.ConcreteModel()

    arcs = [(i, j) for i in range(N) for j in range(N) if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return params["capacity_%d_%d" % (i, j)]

    model.capacity = pyo.Param(model.arcs, initialize=cap_rule, mutable=False)

    def flow_bound_rule(m, i, j):
        return m.flow[i, j] <= m.capacity[i, j]

    model.flow_bound = pyo.Constraint(model.arcs, rule=flow_bound_rule)

    def balance_rule(m, k):
        inflow = sum(m.flow[i, k] for i in range(N) if i != k)
        outflow = sum(m.flow[k, j] for j in range(N) if j != k)
        if k == source:
            return outflow - inflow <= 0
        elif k == sink:
            return inflow - outflow <= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(range(N), rule=balance_rule)

    def obj_rule(m):
        return sum(m.flow[source, j] for j in range(N) if j != source) - \
               sum(m.flow[i, source] for i in range(N) if i != source)

    model.objective_expr = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective_expr))
    return {'objective': obj_val, 'status': 'optimal'}