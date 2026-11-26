import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))

    # Only include arcs that actually exist (capacity key present in params)
    def arc_exists(a, b):
        return ("capacity_%d_%d" % (a, b)) in params

    arcs = [(a, b) for a in nodes for b in nodes if a != b and arc_exists(a, b)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, a, b):
        return params["capacity_%d_%d" % (a, b)]

    model.cap = pyo.Param(model.arcs, initialize=cap_rule, mutable=False)

    model.net_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def inflow(mdl, n):
        return sum(mdl.flow[i, n] for i in nodes if (i, n) in arcs)

    def outflow(mdl, n):
        return sum(mdl.flow[n, j] for j in nodes if (n, j) in arcs)

    def mass_balance_rule(mdl, n):
        if n == 0:
            return outflow(mdl, n) - inflow(mdl, n) == mdl.net_flow
        elif n == 7:
            return inflow(mdl, n) - outflow(mdl, n) == mdl.net_flow
        else:
            return inflow(mdl, n) == outflow(mdl, n)

    model.balance = pyo.Constraint(nodes, rule=mass_balance_rule)

    def ub_rule(mdl, a, b):
        return mdl.flow[a, b] <= mdl.cap[a, b]

    model.upper_bound = pyo.Constraint(model.arcs, rule=ub_rule)

    model.obj = pyo.Objective(expr=model.net_flow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}