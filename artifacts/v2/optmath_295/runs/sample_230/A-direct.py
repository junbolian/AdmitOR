import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    # Structural constants: machine hours consumed per unit of each product
    # for grinders, drills, borers. These are problem-structural (not in PARAMS).
    machine_hours_per_unit = {
        0: (1.0, 1.0, 1.0),
        1: (1.0, 1.0, 2.0),
        2: (2.0, 1.0, 2.0),
    }

    products = list(range(3))
    periods = list(range(6))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.x = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.s = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.i = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(
            profit_per_unit[p] * m.s[p, t] - holding_cost * m.i[p, t]
            for p in m.P
            for t in m.T
        )

    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def balance_first_rule(m, p):
        return m.x[p, 0] == m.s[p, 0] + m.i[p, 0]

    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.i[p, t - 1] + m.x[p, t] == m.s[p, t] + m.i[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(machine_hours_per_unit[p][0] * m.x[p, t] for p in m.P) <= grinder_hours[t]

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(machine_hours_per_unit[p][1] * m.x[p, t] for p in m.P) <= drill_hours[t]

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(machine_hours_per_unit[p][2] * m.x[p, t] for p in m.P) <= borer_hours[t]

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_max_rule(m, p, t):
        return m.i[p, t] <= max_inventory

    model.inv_max = pyo.Constraint(model.P, model.T, rule=inv_max_rule)

    def sales_max_rule(m, p, t):
        return m.s[p, t] <= max_sales[p][t]

    model.sales_max = pyo.Constraint(model.P, model.T, rule=sales_max_rule)

    def final_inv_rule(m, p):
        return m.i[p, 5] == final_inventory[p]

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}