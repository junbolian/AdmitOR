import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit"]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    mh0 = params["machine_hours_product0"]
    mh1 = params["machine_hours_product1"]
    mh2 = params["machine_hours_product2"]
    max_inv = params["max_inventory_per_product"]
    sales_limit = [
        params["sales_limit_product0"],
        params["sales_limit_product1"],
        params["sales_limit_product2"],
    ]
    target_end = params["target_inventory_end"]

    periods = list(range(5))
    products = list(range(3))
    machines = list(range(3))
    machine_hours = {0: mh0, 1: mh1, 2: mh2}
    caps = [grinder_cap, drill_cap, borer_cap]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.J = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=machines)

    model.prod = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[j] * m.sales[t, j] - hold_cost * m.inv[t, j]
            for t in m.P for j in m.J
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance
    def balance_rule(m, t, j):
        if t == 0:
            return m.prod[t, j] == m.sales[t, j] + m.inv[t, j]
        return m.inv[t - 1, j] + m.prod[t, j] == m.sales[t, j] + m.inv[t, j]

    model.balance_con = pyo.Constraint(model.P, model.J, rule=balance_rule)

    # Machine capacity
    def cap_rule(m, t, k):
        return sum(machine_hours[j][k] * m.prod[t, j] for j in m.J) <= caps[k]

    model.cap_con = pyo.Constraint(model.P, model.M, rule=cap_rule)

    # Inventory limits
    def inv_lim_rule(m, t, j):
        return m.inv[t, j] <= max_inv

    model.inv_lim_con = pyo.Constraint(model.P, model.J, rule=inv_lim_rule)

    # Sales limits
    def sales_lim_rule(m, t, j):
        return m.sales[t, j] <= sales_limit[j][t]

    model.sales_lim_con = pyo.Constraint(model.P, model.J, rule=sales_lim_rule)

    # Target ending inventory
    def target_rule(m, j):
        return m.inv[4, j] == target_end

    model.target_con = pyo.Constraint(model.J, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}