import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_fac = len(fixed_costs)
    num_cust = len(demands)

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, num_fac - 1)
    model.CUST = pyo.RangeSet(0, num_cust - 1)

    model.open = pyo.Var(model.FAC, domain=pyo.Binary)
    model.ship = pyo.Var(model.FAC, model.CUST, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_costs[j] * m.open[j] for j in m.FAC) + sum(
            shipping_costs[i][j] * m.ship[j, i]
            for j in m.FAC
            for i in m.CUST
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, i):
        return sum(m.ship[j, i] for j in m.FAC) == demands[i]

    model.demand_con = pyo.Constraint(model.CUST, rule=demand_rule)

    def capacity_rule(m, j):
        return sum(m.ship[j, i] for i in m.CUST) <= capacities[j] * m.open[j]

    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}