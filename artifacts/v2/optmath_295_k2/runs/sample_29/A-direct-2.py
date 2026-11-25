import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_fac = len(fixed_costs)
    n_cust = len(demands)

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, n_fac - 1)
    model.CUST = pyo.RangeSet(0, n_cust - 1)

    model.y = pyo.Var(model.FAC, within=pyo.Binary)
    model.x = pyo.Var(model.FAC, model.CUST, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_costs[i] * m.y[i] for i in m.FAC) + sum(
            shipping_costs[i][j] * m.x[i, j] for i in m.FAC for j in m.CUST
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.FAC) == demands[j]

    model.demand_con = pyo.Constraint(model.CUST, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.CUST) <= capacities[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}