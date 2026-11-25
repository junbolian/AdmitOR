import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    ship_cost = params["ship_cost"]
    capacity = params["capacity"]

    n_fac = len(fixed_cost)
    n_cus = len(demand)
    facilities = range(n_fac)
    customers = range(n_cus)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(facilities, customers, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(facilities, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_cost[i] * m.y[i] for i in facilities) + sum(
            ship_cost[i][j] * m.x[i, j] for i in facilities for j in customers
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in facilities) == demand[j]

    model.demand_con = pyo.Constraint(customers, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in customers) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(facilities, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}