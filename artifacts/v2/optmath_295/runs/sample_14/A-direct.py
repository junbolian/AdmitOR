import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = list(range(4))
    periods = list(range(5))

    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    machine_hours_grinders = params["machine_hours_grinders"]
    machine_hours_drills = params["machine_hours_drills"]
    machine_hours_borers = params["machine_hours_borers"]
    borer_hours_period0 = params["borer_hours_period0"]
    time_per_unit = params["time_per_unit"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_inventory_end = params["target_inventory_end"]

    machine_names = ["grinders", "drills", "borers"]
    machine_capacity = {
        "grinders": machine_hours_grinders,
        "drills": machine_hours_drills,
        "borers": machine_hours_borers,
    }

    model = pyo.ConcreteModel()

    model.PRODUCTS = pyo.Set(initialize=products, ordered=True)
    model.PERIODS = pyo.Set(initialize=periods, ordered=True)

    model.produce = pyo.Var(model.PRODUCTS, model.PERIODS, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.PRODUCTS, model.PERIODS, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.PRODUCTS, model.PERIODS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(
            profit_per_unit[p] * m.sell[p, t]
            for p in m.PRODUCTS
            for t in m.PERIODS
        )
        holding = sum(
            holding_cost_per_unit * m.inventory[p, t]
            for p in m.PRODUCTS
            for t in m.PERIODS
        )
        return revenue - holding

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def initial_balance_rule(m, p):
        return m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.initial_balance = pyo.Constraint(model.PRODUCTS, rule=initial_balance_rule)

    def inventory_balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.inventory_balance = pyo.Constraint(
        model.PRODUCTS, model.PERIODS, rule=inventory_balance_rule
    )

    def grinder_capacity_rule(m, t):
        return sum(
            time_per_unit[p][0] * m.produce[p, t] for p in m.PRODUCTS
        ) <= machine_capacity["grinders"]

    model.grinder_capacity = pyo.Constraint(model.PERIODS, rule=grinder_capacity_rule)

    def drill_capacity_rule(m, t):
        return sum(
            time_per_unit[p][1] * m.produce[p, t] for p in m.PRODUCTS
        ) <= machine_capacity["drills"]

    model.drill_capacity = pyo.Constraint(model.PERIODS, rule=drill_capacity_rule)

    def borer_capacity_rule(m, t):
        if t == 0:
            cap = borer_hours_period0
        else:
            cap = machine_capacity["borers"]
        return sum(
            time_per_unit[p][2] * m.produce[p, t] for p in m.PRODUCTS
        ) <= cap

    model.borer_capacity = pyo.Constraint(model.PERIODS, rule=borer_capacity_rule)

    def inventory_cap_rule(m, p, t):
        return m.inventory[p, t] <= inventory_capacity

    model.inventory_cap = pyo.Constraint(
        model.PRODUCTS, model.PERIODS, rule=inventory_cap_rule
    )

    def sales_limit_rule(m, p, t):
        return m.sell[p, t] <= sales_limit[p][t]

    model.sales_limit_con = pyo.Constraint(
        model.PRODUCTS, model.PERIODS, rule=sales_limit_rule
    )

    def target_inventory_rule(m, p):
        return m.inventory[p, 4] == target_inventory_end[p]

    model.target_inventory = pyo.Constraint(
        model.PRODUCTS, rule=target_inventory_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}