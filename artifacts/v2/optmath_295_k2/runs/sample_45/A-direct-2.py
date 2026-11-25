import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    periods = list(range(4))
    products = list(range(3))

    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    hours_grinder = params["machine_hours_grinder"]
    hours_drill = params["machine_hours_drill"]
    hours_borer = params["machine_hours_borer"]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.production = pyo.Var(model.T, model.P, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T, model.P, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.T, model.P, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        revenue = sum(profit_per_unit[p] * mdl.sales[t, p] for t in mdl.T for p in mdl.P)
        holding = sum(holding_cost * mdl.inventory[t, p] for t in mdl.T for p in mdl.P)
        return revenue - holding

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Initial balance (period 0)
    def initial_balance_rule(mdl, p):
        return mdl.production[0, p] == mdl.sales[0, p] + mdl.inventory[0, p]

    model.initial_balance = pyo.Constraint(model.P, rule=initial_balance_rule)

    # Inventory balance (periods 1..3)
    def balance_rule(mdl, t, p):
        return mdl.inventory[t - 1, p] + mdl.production[t, p] == mdl.sales[t, p] + mdl.inventory[t, p]

    model.balance = pyo.Constraint([t for t in periods if t >= 1], model.P, rule=balance_rule)

    # Machine capacity constraints
    def grinder_rule(mdl, t):
        return sum(hours_grinder[p] * mdl.production[t, p] for p in mdl.P) <= grinder_cap[t]

    def drill_rule(mdl, t):
        return sum(hours_drill[p] * mdl.production[t, p] for p in mdl.P) <= drill_cap[t]

    def borer_rule(mdl, t):
        return sum(hours_borer[p] * mdl.production[t, p] for p in mdl.P) <= borer_cap[t]

    model.grinder_capacity = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_capacity = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_capacity = pyo.Constraint(model.T, rule=borer_rule)

    # Inventory limits
    def inv_limit_rule(mdl, t, p):
        return mdl.inventory[t, p] <= inventory_limit

    model.inventory_limit = pyo.Constraint(model.T, model.P, rule=inv_limit_rule)

    # Sales limits
    def sales_limit_rule(mdl, t, p):
        return mdl.sales[t, p] <= sales_limit[t][p]

    model.sales_limit = pyo.Constraint(model.T, model.P, rule=sales_limit_rule)

    # Target ending inventory
    def target_rule(mdl, p):
        return mdl.inventory[3, p] == target_inventory[p]

    model.target_inventory = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}