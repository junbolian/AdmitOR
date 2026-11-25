import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    installation_cost = params["installation_cost"]
    volume_capacity = params["volume_capacity"]
    customer_demand = params["customer_demand"]
    delivery_cost_matrix = params["delivery_cost_matrix"]

    n_customers = len(customer_demand)
    n_lockers = len(installation_cost)
    customers = range(n_customers)
    lockers = range(n_lockers)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(customers, lockers, domain=pyo.Binary)
    model.y = pyo.Var(lockers, domain=pyo.Binary)

    def obj_rule(m):
        fixed = sum(installation_cost[j] * m.y[j] for j in lockers)
        assign = sum(delivery_cost_matrix[i][j] * m.x[i, j]
                     for i in customers for j in lockers)
        return fixed + assign

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in lockers) == 1

    model.assign_con = pyo.Constraint(customers, rule=assign_rule)

    def cap_rule(m, j):
        return sum(customer_demand[i] * m.x[i, j] for i in customers) <= volume_capacity[j] * m.y[j]

    model.cap_con = pyo.Constraint(lockers, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}