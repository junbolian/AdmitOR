import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    periods = list(range(4))
    products = list(range(3))
    machines = ["grinder", "drill", "borer"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.J = pyo.Set(initialize=products)

    model.prod = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[j] * m.sales[t, j] for t in m.P for j in m.J
        ) - sum(
            holding_cost * m.inv[t, j] for t in m.P for j in m.J
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_p0(m, j):
        return m.prod[0, j] == m.sales[0, j] + m.inv[0, j]

    model.balance_p0 = pyo.Constraint(model.J, rule=balance_p0)

    def balance_mid(m, t, j):
        return m.inv[t - 1, j] + m.prod[t, j] == m.sales[t, j] + m.inv[t, j]

    model.balance_mid = pyo.Constraint(
        [t for t in periods if t >= 1], model.J, rule=balance_mid
    )

    def grind_cap(m, t):
        return (
            machine_hours_per_unit[0][0] * m.prod[t, 0]
            + machine_hours_per_unit[0][1] * m.prod[t, 1]
            + machine_hours_per_unit[0][2] * m.prod[t, 2]
            <= grinder_capacity[t]
        )

    model.grind_cap = pyo.Constraint(model.P, rule=grind_cap)

    def drill_cap(m, t):
        return (
            machine_hours_per_unit[1][0] * m.prod[t, 0]
            + machine_hours_per_unit[1][1] * m.prod[t, 1]
            + machine_hours_per_unit[1][2] * m.prod[t, 2]
            <= drill_capacity[t]
        )

    model.drill_cap = pyo.Constraint(model.P, rule=drill_cap)

    def borer_cap(m, t):
        return (
            machine_hours_per_unit[2][0] * m.prod[t, 0]
            + machine_hours_per_unit[2][1] * m.prod[t, 1]
            + machine_hours_per_unit[2][2] * m.prod[t, 2]
            <= borer_capacity[t]
        )

    model.borer_cap = pyo.Constraint(model.P, rule=borer_cap)

    def inv_limit(m, t, j):
        return m.inv[t, j] <= inventory_capacity

    model.inv_limit = pyo.Constraint(model.P, model.J, rule=inv_limit)

    def sales_lim(m, t, j):
        return m.sales[t, j] <= sales_limit[t][j]

    model.sales_lim = pyo.Constraint(model.P, model.J, rule=sales_lim)

    def target_rule(m, j):
        return m.inv[3, j] == target_inventory[j]

    model.target_rule = pyo.Constraint(model.J, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}