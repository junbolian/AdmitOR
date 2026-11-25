import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(8))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.city_set = pyo.Set(initialize=cities)

    def flow_bounds(mdl, i, j):
        return (0.0, float(params["cap_%d_to_%d" % (i, j)]))

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals,
                         bounds=flow_bounds)

    def obj_rule(mdl):
        return sum(float(params["cost_%d_to_%d" % (i, j)]) * mdl.flow[i, j]
                   for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    net_demand = params["net_demand"]

    def balance_rule(mdl, k):
        outflow = sum(mdl.flow[k, j] for j in cities if j != k)
        inflow = sum(mdl.flow[i, k] for i in cities if i != k)
        return outflow - inflow == float(net_demand[k])

    model.balance = pyo.Constraint(model.city_set, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}