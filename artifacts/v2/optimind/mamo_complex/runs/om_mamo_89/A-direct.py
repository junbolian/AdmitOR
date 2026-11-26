import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5, 6]
    source = 0
    sink = 6

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cap(i, j):
        return params["c{}{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap(i, j)

    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    model.obj_var = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(mdl, n):
        inflow = sum(mdl.flow[i, n] for i in nodes if i != n)
        outflow = sum(mdl.flow[n, j] for j in nodes if j != n)
        if n == source:
            return outflow - inflow == mdl.obj_var
        elif n == sink:
            return inflow - outflow == mdl.obj_var
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    model.objective = pyo.Objective(expr=model.obj_var, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))

    return {"objective": obj_val, "status": "optimal"}