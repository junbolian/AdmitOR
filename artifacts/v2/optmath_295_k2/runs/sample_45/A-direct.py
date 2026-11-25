import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    hours_grinder = params["machine_hours_grinder"]
    hours_drill = params["machine_hours_drill"]
    hours_borer = params["machine_hours_borer"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    periods = list(range(4))
    products = list(range(3))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.J = pyo.Set(initialize=products)

    model.prod = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    # Objective: maximize profit from sales minus holding cost
    model.obj = pyo.Objective(
        expr=sum(profit_per_unit[j] * model.sale[p, j] for p in model.P for j in model.J)
        - sum(holding_cost * model.inv[p, j] for p in model.P for j in model.J),
        sense=pyo.maximize,
    )

    # Initial balance (period 0)
    def initial_balance_rule(m, j):
        return m.prod[0, j] == m.sale[0, j] + m.inv[0, j]

    model.initial_balance = pyo.Constraint(model.J, rule=initial_balance_rule)

    # Inventory balance (periods 1..3)
    def inv_balance_rule(m, p, j):
        return m.prod[p, j] + m.inv[p - 1, j] == m.sale[p, j] + m.inv[p, j]

    model.inv_balance = pyo.Constraint(
        [p for p in periods if p >= 1], model.J, rule=inv_balance_rule
    )

    # Machine capacity constraints
    def grinder_rule(m, p):
        return sum(hours_grinder[j] * m.prod[p, j] for j in m.J) <= grinder_capacity[p]

    def drill_rule(m, p):
        return sum(hours_drill[j] * m.prod[p, j] for j in m.J) <= drill_capacity[p]

    def borer_rule(m, p):
        return sum(hours_borer[j] * m.prod[p, j] for j in m.J) <= borer_capacity[p]

    model.grinder_cap = pyo.Constraint(model.P, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.P, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.P, rule=borer_rule)

    # Inventory limits
    def inv_limit_rule(m, p, j):
        return m.inv[p, j] <= inventory_limit

    model.inv_limit = pyo.Constraint(model.P, model.J, rule=inv_limit_rule)

    # Sales limits
    def sale_limit_rule(m, p, j):
        return m.sale[p, j] <= sales_limit[p][j]

    model.sale_limit = pyo.Constraint(model.P, model.J, rule=sale_limit_rule)

    # Target ending inventory at period 3
    def target_inv_rule(m, j):
        return m.inv[3, j] == target_inventory[j]

    model.target_inv = pyo.Constraint(model.J, rule=target_inv_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}