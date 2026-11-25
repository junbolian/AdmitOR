import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 6
    periods = list(range(1, T + 1))

    fixed_setup_cost = params["fixed_setup_cost"]
    variable_production_cost = params["variable_production_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    backlogging_cost = params["backlogging_cost"]
    demand = params["demand"]
    production_capacity = params["production_capacity"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.P, domain=pyo.Binary)
    model.inventory = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return (
            sum(fixed_setup_cost[t - 1] * m.setup[t] for t in m.P)
            + sum(variable_production_cost[t - 1] * m.produce[t] for t in m.P)
            + sum(inventory_holding_cost[t - 1] * m.inventory[t] for t in m.P)
            + sum(backlogging_cost[t - 1] * m.backlog[t] for t in m.P)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, t):
        return m.produce[t] <= production_capacity * m.setup[t]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def balance_rule(m, t):
        prev_inv = m.inventory[t - 1] if t > 1 else 0
        prev_back = m.backlog[t - 1] if t > 1 else 0
        next_inv = m.inventory[t] if t < T else 0
        next_back = m.backlog[t] if t < T else 0
        return prev_inv + m.produce[t] + next_back == demand[t - 1] + next_inv + prev_back

    model.balance_con = pyo.Constraint(model.P, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}