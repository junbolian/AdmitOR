import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    startup_cost = params["startup_cost"]
    startup_scaling_factor = params["startup_scaling_factor"]
    machine_capacity = params["machine_capacity"]
    holding_cost = params["holding_cost"]
    backlog_cost = params["backlog_cost"]
    demand_period0 = params["demand_period0"]

    items = [0, 1, 2]
    periods = [0, 1, 2, 3, 4]

    demand = {}
    for i in items:
        for t in periods:
            demand[i, t] = demand_period0[i]

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=items)
    model.period_set = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.item_set, model.period_set, domain=pyo.Binary)
    model.startup = pyo.Var(model.item_set, model.period_set, domain=pyo.Binary)

    model.prod_qty = pyo.Var(model.item_set, model.period_set, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.item_set, model.period_set, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.item_set, model.period_set, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        total = 0
        for i in m.item_set:
            for t in m.period_set:
                total += production_cost * m.produce[i, t]
                total += startup_cost * m.startup[i, t]
                total += holding_cost[i] * m.inventory[i, t]
                total += backlog_cost[i] * m.backlog[i, t]
        return total

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, t):
        return sum(m.prod_qty[i, t] for i in m.item_set) + \
               startup_scaling_factor * sum(m.startup[i, t] for i in m.item_set) <= machine_capacity

    model.capacity_con = pyo.Constraint(model.period_set, rule=capacity_rule)

    def one_item_rule(m, t):
        return sum(m.produce[i, t] for i in m.item_set) <= 1

    model.one_item_con = pyo.Constraint(model.period_set, rule=one_item_rule)

    def prod_link_rule(m, i, t):
        return m.prod_qty[i, t] <= machine_capacity * m.produce[i, t]

    model.prod_link_con = pyo.Constraint(model.item_set, model.period_set, rule=prod_link_rule)

    def startup_link_rule(m, i, t):
        if t == 0:
            return m.startup[i, t] >= m.produce[i, t]
        return m.startup[i, t] >= m.produce[i, t] - m.produce[i, t - 1]

    model.startup_link_con = pyo.Constraint(model.item_set, model.period_set, rule=startup_link_rule)

    def balance_rule(m, i, t):
        if t == 0:
            prev_inv = 0
            prev_backlog = 0
        else:
            prev_inv = m.inventory[i, t - 1]
            prev_backlog = m.backlog[i, t - 1]
        return prev_inv - prev_backlog + m.prod_qty[i, t] == demand[i, t] + m.inventory[i, t] - m.backlog[i, t]

    model.balance_con = pyo.Constraint(model.item_set, model.period_set, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}