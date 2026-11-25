import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()

    products = ['product_0', 'product_1', 'product_2']
    periods = [0, 1, 2, 3]

    revenue = {
        'product_0': params["revenue_product_0"],
        'product_1': params["revenue_product_1"],
        'product_2': params["revenue_product_2"],
    }
    holding_cost = params["holding_cost"]

    grinder_cap = {
        0: params["grinder_capacity_period_0"],
        1: params["grinder_capacity_periods_1_3"],
        2: params["grinder_capacity_periods_1_3"],
        3: params["grinder_capacity_periods_1_3"],
    }
    drill_cap = {
        0: params["drill_capacity_periods_0_1_3"],
        1: params["drill_capacity_periods_0_1_3"],
        2: params["drill_capacity_period_2"],
        3: params["drill_capacity_periods_0_1_3"],
    }
    borer_cap = params["borer_capacity_all_periods"]
    max_inv = params["max_inventory_per_product_per_period"]

    sales_limit = {
        0: {
            'product_0': params["sales_limit_p0"],
            'product_1': params["sales_limit_p0"],
            'product_2': params["sales_limit_p0"],
        },
        1: {
            'product_0': params["sales_limit_p1"],
            'product_1': params["sales_limit_p1"],
            'product_2': params["sales_limit_p1"],
        },
        2: {
            'product_0': params["sales_limit_p2"],
            'product_1': params["sales_limit_p2"],
            'product_2': params["sales_limit_p2"],
        },
        3: {
            'product_0': params["sales_limit_p3"],
            'product_1': params["sales_limit_p3"],
            'product_2': params["sales_limit_p3"],
        },
    }
    final_inv = params["final_inventory_required"]

    grinder_usage = {'product_0': 1, 'product_1': 2, 'product_2': 1}
    drill_usage = {'product_0': 2, 'product_1': 1, 'product_2': 3}
    borer_usage = {'product_0': 2, 'product_1': 2, 'product_2': 2}

    model.PRODUCTS = pyo.Set(initialize=products)
    model.PERIODS = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.PRODUCTS, model.PERIODS, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.PRODUCTS, model.PERIODS, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.PRODUCTS, model.PERIODS, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(md, p, t):
        if t == 0:
            return md.produce[p, t] == md.sell[p, t] + md.inventory[p, t]
        return md.inventory[p, t - 1] + md.produce[p, t] == md.sell[p, t] + md.inventory[p, t]

    model.inventory_balance = pyo.Constraint(model.PRODUCTS, model.PERIODS, rule=inventory_balance_rule)

    def grinder_rule(md, t):
        return sum(grinder_usage[p] * md.produce[p, t] for p in md.PRODUCTS) <= grinder_cap[t]

    model.grinder_capacity = pyo.Constraint(model.PERIODS, rule=grinder_rule)

    def drill_rule(md, t):
        return sum(drill_usage[p] * md.produce[p, t] for p in md.PRODUCTS) <= drill_cap[t]

    model.drill_capacity = pyo.Constraint(model.PERIODS, rule=drill_rule)

    def borer_rule(md, t):
        return sum(borer_usage[p] * md.produce[p, t] for p in md.PRODUCTS) <= borer_cap

    model.borer_capacity = pyo.Constraint(model.PERIODS, rule=borer_rule)

    def max_inventory_rule(md, p, t):
        return md.inventory[p, t] <= max_inv

    model.max_inventory = pyo.Constraint(model.PRODUCTS, model.PERIODS, rule=max_inventory_rule)

    def sales_limit_rule(md, p, t):
        return md.sell[p, t] <= sales_limit[t][p]

    model.sales_limit = pyo.Constraint(model.PRODUCTS, model.PERIODS, rule=sales_limit_rule)

    def final_inventory_rule(md, p):
        return md.inventory[p, 3] == final_inv

    model.final_inventory = pyo.Constraint(model.PRODUCTS, rule=final_inventory_rule)

    def objective_rule(md):
        revenue_term = sum(revenue[p] * md.sell[p, t] for p in md.PRODUCTS for t in md.PERIODS)
        holding_term = sum(holding_cost * md.inventory[p, t] for p in md.PRODUCTS for t in md.PERIODS)
        return revenue_term - holding_term

    model.profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.profit))
    except Exception:
        return {'objective': None, 'status': 'infeasible or solve failed'}

    return {'objective': obj_val, 'status': 'optimal'}