import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    n_fac = len(fixed_costs)
    n_cus = len(demands)

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, n_fac - 1)
    model.CUS = pyo.RangeSet(0, n_cus - 1)

    model.x = pyo.Var(model.FAC, model.CUS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.FAC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_costs[i] * m.y[i] for i in m.FAC) + sum(
            shipping_costs[i][j] * m.x[i, j] for i in m.FAC for j in m.CUS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.FAC) == demands[j]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.CUS) <= capacities[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}