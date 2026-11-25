import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    resource_usage = params["resource_usage"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    products = list(range(len(demand)))
    weeks = list(range(len(demand[0])))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.W = pyo.Set(initialize=weeks)

    # Decision variables
    model.produce = pyo.Var(model.P, model.W, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.W, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.P, model.W, domain=pyo.Binary)

    def obj_rule(m):
        return (
            sum(production_cost[p][w] * m.produce[p, w] for p in m.P for w in m.W)
            + sum(setup_cost[p][w] * m.setup[p, w] for p in m.P for w in m.W)
            + sum(holding_cost * m.inventory[p, w] for p in m.P for w in m.W)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Inventory balance: starting inv + production - ending inv = demand
    def balance_rule(m, p, w):
        prev_inv = m.inventory[p, w - 1] if w > 0 else 0
        return prev_inv + m.produce[p, w] - m.inventory[p, w] == demand[p][w]

    model.balance = pyo.Constraint(model.P, model.W, rule=balance_rule)

    # Resource capacity per week
    def resource_rule(m, w):
        return sum(resource_usage[p] * m.produce[p, w] for p in m.P) <= resource_capacity[w]

    model.resource = pyo.Constraint(model.W, rule=resource_rule)

    # Production limit per product per week
    def limit_rule(m, p, w):
        return m.produce[p, w] <= production_limit[p][w]

    model.limit = pyo.Constraint(model.P, model.W, rule=limit_rule)

    # Setup linking: production only if setup activated
    def setup_link_rule(m, p, w):
        return m.produce[p, w] <= production_limit[p][w] * m.setup[p, w]

    model.setup_link = pyo.Constraint(model.P, model.W, rule=setup_link_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}