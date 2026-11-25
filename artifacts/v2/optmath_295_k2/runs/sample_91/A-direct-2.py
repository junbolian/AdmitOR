import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1, 2]
    months = [0, 1, 2, 3]
    machine_types = ["grinders", "drills", "borers"]

    profit = {
        0: params["profit_per_unit_product_0"],
        1: params["profit_per_unit_product_1"],
        2: params["profit_per_unit_product_2"],
    }
    hold_cost = params["holding_cost_per_unit_per_month"]

    machine_hours_available = {
        "grinders": params["machine_hours_available_grinders"],
        "drills": params["machine_hours_available_drills"],
        "borers": params["machine_hours_available_borers"],
    }
    time_required = {
        "grinders": {
            0: params["time_grinders_product_0"],
            1: params["time_grinders_product_1"],
            2: params["time_grinders_product_2"],
        },
        "drills": {
            0: params["time_drills_product_0"],
            1: params["time_drills_product_1"],
            2: params["time_drills_product_2"],
        },
        "borers": {
            0: params["time_borers_product_0"],
            1: params["time_borers_product_1"],
            2: params["time_borers_product_2"],
        },
    }

    max_inventory = params["max_inventory_per_product"]
    sales_limits = {
        0: params["sales_limits_product_0"],
        1: params["sales_limits_product_1"],
        2: params["sales_limits_product_2"],
    }
    target_final_inventory = params["target_inventory_end_horizon"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products, ordered=True)
    model.M = pyo.Set(initialize=months, ordered=True)
    model.K = pyo.Set(initialize=machine_types, ordered=True)

    model.prod = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(profit[p] * m.sales[p, t] for p in m.P for t in m.M)
        holding = sum(hold_cost * m.inv[p, t] for p in m.P for t in m.M)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Initial inventory balance: month 0
    def balance_initial_rule(m, p):
        return m.prod[p, 0] == m.sales[p, 0] + m.inv[p, 0]

    model.balance_initial = pyo.Constraint(model.P, rule=balance_initial_rule)

    # Monthly inventory balance: months 1..3
    def balance_monthly_rule(m, p, t):
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]

    model.balance_monthly = pyo.Constraint(
        model.P, list(range(1, 4)), rule=balance_monthly_rule
    )

    # Machine capacity constraints
    def machine_cap_rule(m, k, t):
        usage = sum(time_required[k][p] * m.prod[p, t] for p in m.P)
        return usage <= machine_hours_available[k][t]

    model.machine_cap = pyo.Constraint(
        model.K, model.M, rule=machine_cap_rule
    )

    # Inventory storage limits
    def inventory_limit_rule(m, p, t):
        return m.inv[p, t] <= max_inventory

    model.inventory_limit = pyo.Constraint(
        model.P, model.M, rule=inventory_limit_rule
    )

    # Sales limits
    def sales_limit_rule(m, p, t):
        return m.sales[p, t] <= sales_limits[p][t]

    model.sales_limit = pyo.Constraint(model.P, model.M, rule=sales_limit_rule)

    # Final inventory target at end of month 3
    def final_inventory_rule(m, p):
        return m.inv[p, 3] == target_final_inventory

    model.final_inventory = pyo.Constraint(model.P, rule=final_inventory_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}