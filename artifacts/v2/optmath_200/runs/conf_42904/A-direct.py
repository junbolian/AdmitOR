import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_capacity = params["machine_capacity"]
    time_grinders = params["time_grinders"]
    time_drills = params["time_drills"]
    time_borers = params["time_borers"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    num_products = 4
    num_periods = 6

    products = list(range(num_products))
    periods = list(range(num_periods))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.production = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        revenue = sum(
            profit_per_unit[p] * mdl.sales[p, t]
            for p in mdl.P for t in mdl.T
        )
        holding = sum(
            holding_cost * mdl.inventory[p, t]
            for p in mdl.P for t in mdl.T
        )
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first_rule(mdl, p):
        return mdl.production[p, 0] == mdl.sales[p, 0] + mdl.inventory[p, 0]

    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)

    def balance_rule(mdl, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return (
            mdl.inventory[p, t - 1] + mdl.production[p, t]
            == mdl.sales[p, t] + mdl.inventory[p, t]
        )

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(mdl, t):
        return sum(
            time_grinders[p] * mdl.production[p, t] for p in mdl.P
        ) <= machine_capacity[0]

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(
            time_drills[p] * mdl.production[p, t] for p in mdl.P
        ) <= machine_capacity[1]

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        return sum(
            time_borers[p] * mdl.production[p, t] for p in mdl.P
        ) <= machine_capacity[2]

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_limit_rule(mdl, p, t):
        return mdl.inventory[p, t] <= inventory_limit

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sales_limit_rule(mdl, p, t):
        return mdl.sales[p, t] <= sales_limit[p][t]

    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def target_rule(mdl, p):
        return mdl.inventory[p, num_periods - 1] == target_inventory[p]

    model.target = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}