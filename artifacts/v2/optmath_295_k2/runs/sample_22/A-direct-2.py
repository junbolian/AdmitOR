import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit_per_period = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    machine_time_grinder = params["machine_time_grinder"]
    machine_time_drill = params["machine_time_drill"]
    machine_time_borer = params["machine_time_borer"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_final_inventory = params["target_final_inventory"]

    products = range(3)
    periods = range(5)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(products))
    model.T = pyo.Set(initialize=list(periods))

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(
            profit_per_unit[p] * m.sales[p, t] for p in m.P for t in m.T
        )
        holding = sum(
            holding_cost_per_unit_per_period * m.inv[p, t]
            for p in m.P
            for t in m.T
        )
        return revenue - holding

    model.OBJ = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Initial balance: Period 0
    def init_balance_rule(m, p):
        return m.prod[p, 0] == m.sales[p, 0] + m.inv[p, 0]

    model.init_balance = pyo.Constraint(model.P, rule=init_balance_rule)

    # Inventory balance: Periods 1-4
    def inv_balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]

    model.inv_balance = pyo.Constraint(model.P, model.T, rule=inv_balance_rule)

    # Final inventory target
    def final_inv_rule(m, p):
        return m.inv[p, 4] == target_final_inventory[p]

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    # Inventory capacity
    def inv_cap_rule(m, p, t):
        return m.inv[p, t] <= inventory_capacity

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    # Sales limits
    def sales_limit_rule(m, p, t):
        return m.sales[p, t] <= sales_limit[p][t]

    model.sales_limit_con = pyo.Constraint(
        model.P, model.T, rule=sales_limit_rule
    )

    # Machine capacity constraints
    def grinder_rule(m, t):
        return (
            sum(machine_time_grinder[p] * m.prod[p, t] for p in m.P)
            <= grinder_hours[t]
        )

    model.grinder_con = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return (
            sum(machine_time_drill[p] * m.prod[p, t] for p in m.P)
            <= drill_hours[t]
        )

    model.drill_con = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return (
            sum(machine_time_borer[p] * m.prod[p, t] for p in m.P)
            <= borer_hours[t]
        )

    model.borer_con = pyo.Constraint(model.T, rule=borer_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.OBJ))
    return {"objective": obj_val, "status": "optimal"}