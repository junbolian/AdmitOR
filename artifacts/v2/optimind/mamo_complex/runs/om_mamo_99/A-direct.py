import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5]
    source = 0
    sink = 5

    arcs = []
    for i in nodes:
        for j in nodes:
            if i != j:
                key = "capacity_{}_{}".format(i, j)
                if key in params and params[key] > 0:
                    arcs.append((i, j))

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    def cap_init(mdl, i, j):
        return float(params["capacity_{}_{}".format(i, j)])

    model.capacity = pyo.Param(model.arcs, initialize=cap_init, within=pyo.NonNegativeReals)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def flow_balance_rule(mdl, k):
        lhs = 0
        for (i, j) in arcs:
            if j == k:
                lhs += mdl.flow[i, j]
            if i == k:
                lhs -= mdl.flow[i, j]
        rhs = 0
        if k == source:
            rhs = mdl.net_out
        if k == sink:
            rhs = -mdl.net_out
        return lhs == rhs

    # Introduce net flow variable so source/sink balances are free but consistent
    model.net_out = pyo.Var(domain=pyo.NonNegativeReals)
    model.balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity[i, j]

    model.cap_limit = pyo.Constraint(model.arcs, rule=cap_rule)

    def obj_rule(mdl):
        return mdl.net_out

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}