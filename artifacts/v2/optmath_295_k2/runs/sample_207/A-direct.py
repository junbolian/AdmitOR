import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    weeks = list(range(1, 8))
    products = ['A', 'B']

    demand = {
        'A': params["demand_A"],
        'B': params["demand_B"],
    }
    prod_cost = {
        'A': params["prod_cost_A"],
        'B': params["prod_cost_B"],
    }
    setup_cost = {
        'A': params["setup_cost_A"],
        'B': params["setup_cost_B"],
    }
    hold_cost = {
        'A': params["hold_cost_A"],
        'B': params["hold_cost_B"],
    }
    capacity = params["capacity"]
    resource_use = {
        'A': params["resource_use_A"],
        'B': params["resource_use_B"],
    }
    max_prod = {
        'A': params["max_prod_A"],
        'B': params["max_prod_B"],
    }

    model = pyo.ConcreteModel()

    model.WEEKS = pyo.Set(initialize=weeks, ordered=True)
    model.PRODUCTS = pyo.Set(initialize=products, ordered=True)

    model.produce = pyo.Var(model.PRODUCTS, model.WEEKS, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.PRODUCTS, model.WEEKS, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.PRODUCTS, model.WEEKS, domain=pyo.Binary)

    def obj_rule(m):
        total = 0.0
        for p in m.PRODUCTS:
            for w in m.WEEKS:
                total += prod_cost[p][w - 1] * m.produce[p, w]
                total += setup_cost[p][w - 1] * m.setup[p, w]
                total += hold_cost[p][w - 1] * m.inventory[p, w]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, p, w):
        prev_inv = m.inventory[p, w - 1] if w > 1 else 0.0
        return prev_inv + m.produce[p, w] - m.inventory[p, w] == demand[p][w - 1]

    model.balance_con = pyo.Constraint(model.PRODUCTS, model.WEEKS, rule=balance_rule)

    def setup_link_rule(m, p, w):
        return m.produce[p, w] <= max_prod[p][w - 1] * m.setup[p, w]

    model.setup_link_con = pyo.Constraint(model.PRODUCTS, model.WEEKS, rule=setup_link_rule)

    def capacity_rule(m, w):
        return sum(resource_use[p] * m.produce[p, w] for p in m.PRODUCTS) <= capacity[w - 1]

    model.capacity_con = pyo.Constraint(model.WEEKS, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}