import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_dc = len(opening_costs)
    n_store = len(demands)

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, n_dc - 1)
    model.STORE = pyo.RangeSet(0, n_store - 1)

    model.y = pyo.Var(model.DC, domain=pyo.Binary)
    model.x = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_costs[i] * m.y[i] for i in m.DC) + \
               sum(transport_costs[i][j] * m.x[i, j] for i in m.DC for j in m.STORE)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.DC) == demands[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.STORE) <= capacities[i] * m.y[i]

    model.cap_con = pyo.Constraint(model.DC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}