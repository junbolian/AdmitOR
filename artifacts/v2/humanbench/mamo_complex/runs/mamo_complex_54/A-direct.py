import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(dimen=2, initialize=arcs)

    def cap_init(mdl, i, j):
        return params["capacity_{}_{}".format(i, j)]

    model.capacity = pyo.Param(model.arcs, initialize=cap_init)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    source = 0
    sink = 5

    def flow_balance_rule(mdl, k):
        out_flow = sum(mdl.flow[k, j] for j in cities if j != k)
        in_flow = sum(mdl.flow[i, k] for i in cities if i != k)
        if k == source:
            return out_flow - in_flow >= 0
        if k == sink:
            return in_flow - out_flow >= 0
        return out_flow - in_flow == 0

    model.balance = pyo.Constraint(cities, rule=flow_balance_rule)

    def upper_bound_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity[i, j]

    model.cap_con = pyo.Constraint(model.arcs, rule=upper_bound_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[i, sink] for i in cities if i != sink) - \
               sum(mdl.flow[sink, j] for j in cities if j != sink)

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}