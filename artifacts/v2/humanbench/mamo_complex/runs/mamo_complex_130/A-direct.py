import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock = params["stock"]
    need = params["need"]
    cost = params["cost"]

    n = len(stock)
    regions = list(range(n))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=regions)
    model.J = pyo.Set(initialize=regions)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J if i != j)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J if j != i) <= stock[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, i):
        return sum(m.x[j, i] for j in m.J if j != i) + stock[i] >= need[i]

    model.demand_con = pyo.Constraint(model.I, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}