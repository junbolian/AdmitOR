import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = 7
    num_centers = 6

    supply = [params[f"supply_{i}"] for i in range(num_facilities)]
    demand = [params[f"demand_{j}"] for j in range(num_centers)]
    cost = [[params[f"cost_{i}"][j] for j in range(num_centers)] for i in range(num_facilities)]
    cap = [[params[f"cap_{i}"][j] for j in range(num_centers)] for i in range(num_facilities)]

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, num_facilities - 1)
    model.C = pyo.RangeSet(0, num_centers - 1)

    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.F for j in m.C)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= supply[i]

    model.supply_con = pyo.Constraint(model.F, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.F) >= demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= cap[i][j]

    model.cap_con = pyo.Constraint(model.F, model.C, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}