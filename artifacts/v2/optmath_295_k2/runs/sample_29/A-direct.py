import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = len(fixed_costs)
    num_customers = len(demands)
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facilities)
    model.C = pyo.Set(initialize=customers)

    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.F, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_costs[i] * m.y[i] for i in m.F) + sum(
            shipping_costs[i][j] * m.x[i, j] for i in m.F for j in m.C
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.F) == demands[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacities[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.F, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}