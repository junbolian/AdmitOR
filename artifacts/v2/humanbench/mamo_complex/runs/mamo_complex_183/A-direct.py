import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    centers = list(range(1, 7))
    stores = list(range(1, 10))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=centers)
    model.J = pyo.Set(initialize=stores)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, domain=pyo.Binary)

    def obj_rule(m):
        return sum(opening_costs[i - 1] * m.y[i] for i in m.I) + \
               sum(transport_costs[i - 1][j - 1] * m.x[i, j] for i in m.I for j in m.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demands[j - 1]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= capacities[i - 1] * m.y[i]

    model.cap_con = pyo.Constraint(model.I, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}