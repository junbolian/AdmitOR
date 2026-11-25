import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def sales_limit_rule(model, p, t):
        if p == 0:
            return model.sales[p, t] <= sales_limit_product0[t]
        return model.sales[p, t] <= sales_limit_product1[t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    model.inv_limit = pyo.Constraint(
        model.P, model.T, rule=lambda model, p, t: model.inv[p, t] <= inventory_limit
    )

    def balance_rule(model, p, t):
        if t == 0:
            return model.prod[p, t] == model.sales[p, t] + model.inv[p, t]
        return model.inv[p, t - 1] + model.prod[p, t] == model.sales[p, t] + model.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    model.target = pyo.Constraint(
        model.P, rule=lambda model, p: model.inv[p, 3] == target_inventory
    )

    def grinder_rule(model, t):
        return (
            sum(machine_hours_per_unit["grinders"] * model.prod[p, t] for p in model.P)
            <= grinder_capacity[t]
        )

    def drill_rule(model, t):
        return (
            sum(machine_hours_per_unit["drills"] * model.prod[p, t] for p in model.P)
            <= drill_capacity[t]
        )

    def borer_rule(model, t):
        return (
            sum(machine_hours_per_unit["borers"] * model.prod[p, t] for p in model.P)
            <= borer_capacity[t]
        )

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def obj_rule(model):
        return sum(
            profit_per_unit[p] * model.sales[p, t] - holding_cost * model.inv[p, t]
            for p in model.P
            for t in model.T
        )

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.objective))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}