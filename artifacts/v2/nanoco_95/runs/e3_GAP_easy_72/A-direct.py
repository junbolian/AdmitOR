import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    orders = list(range(7))
    dcs = ['DC1', 'DC2', 'DC3']

    space = {
        'DC1': [params["space_DC1"][i] for i in orders],
        'DC2': [params["space_DC2"][i] for i in orders],
        'DC3': [params["space_DC3"][i] for i in orders],
    }
    cost = {
        'DC1': [params["cost_DC1"][i] for i in orders],
        'DC2': [params["cost_DC2"][i] for i in orders],
        'DC3': [params["cost_DC3"][i] for i in orders],
    }
    cap = {
        'DC1': params["capacity_DC1"],
        'DC2': params["capacity_DC2"],
        'DC3': params["capacity_DC3"],
    }

    model = pyo.ConcreteModel()

    model.ORDERS = pyo.Set(initialize=orders)
    model.DCS = pyo.Set(initialize=dcs)

    model.x = pyo.Var(model.ORDERS, model.DCS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(cost[d][i] * m.x[i, d] for i in orders for d in dcs)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, d] for d in dcs) == 1

    model.assign = pyo.Constraint(model.ORDERS, rule=assign_rule)

    def capacity_rule(m, d):
        return sum(space[d][i] * m.x[i, d] for i in orders) <= cap[d]

    model.cap = pyo.Constraint(model.DCS, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {'objective': obj_val, 'status': 'optimal'}