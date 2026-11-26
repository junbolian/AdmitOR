import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    months = list(range(6))

    model = pyo.ConcreteModel()
    model.M = pyo.Set(initialize=months, ordered=True)

    demand = params["demand"]

    # Variables
    model.produce = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.outsource = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.hire = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.fire = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.workforce = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.backorder = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.M, within=pyo.NonNegativeReals)

    # Objective: maximize net profit
    def obj_rule(m):
        revenue = sum(params["sales_price"] * m.sales[t] for t in m.M)
        raw = sum(params["raw_material_cost"] * m.produce[t] for t in m.M)
        out = sum(params["outsourcing_cost"] * m.outsource[t] for t in m.M)
        hold = sum(params["inventory_holding_cost"] * m.inventory[t] for t in m.M)
        back = sum(params["backorder_cost"] * m.backorder[t] for t in m.M)
        reg_wage = sum(
            params["regular_hours_per_worker"] * params["regular_wage_per_hour"] * m.workforce[t]
            for t in m.M
        )
        ot_wage = sum(params["overtime_wage_per_hour"] * m.overtime[t] for t in m.M)
        hire_c = sum(params["hiring_cost"] * m.hire[t] for t in m.M)
        fire_c = sum(params["firing_cost"] * m.fire[t] for t in m.M)
        return revenue - raw - out - hold - back - reg_wage - ot_wage - hire_c - fire_c

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Workforce balance
    def workforce_rule(m, t):
        if t == 0:
            return m.workforce[t] == params["initial_workforce"] + m.hire[t] - m.fire[t]
        return m.workforce[t] == m.workforce[t - 1] + m.hire[t] - m.fire[t]

    model.workforce_balance = pyo.Constraint(model.M, rule=workforce_rule)

    # Inventory / backorder balance:
    # inventory[t] + backorder[t] = inventory[t-1] + backorder[t-1] + produce[t] + outsource[t] - demand[t]
    def inv_rule(m, t):
        if t == 0:
            lhs = m.inventory[t] + m.backorder[t]
            rhs = params["initial_inventory"] + m.produce[t] + m.outsource[t] - demand[t]
            return lhs == rhs
        lhs = m.inventory[t] + m.backorder[t]
        rhs = m.inventory[t - 1] + m.backorder[t - 1] + m.produce[t] + m.outsource[t] - demand[t]
        return lhs == rhs

    model.inv_balance = pyo.Constraint(model.M, rule=inv_rule)

    # Labor capacity (regular + overtime hours)
    def labor_rule(m, t):
        return (
            params["labor_hours_per_unit"] * m.produce[t]
            <= params["regular_hours_per_worker"] * m.workforce[t] + m.overtime[t]
        )

    model.labor_cap = pyo.Constraint(model.M, rule=labor_rule)

    # Overtime limit
    def ot_rule(m, t):
        return m.overtime[t] <= params["max_overtime_hours_per_worker"] * m.workforce[t]

    model.ot_limit = pyo.Constraint(model.M, rule=ot_rule)

    # Sales cannot exceed demand
    def sales_rule(m, t):
        return m.sales[t] <= demand[t]

    model.sales_limit = pyo.Constraint(model.M, rule=sales_rule)

    # Inventory and backorder cannot both be positive
    def no_simultaneous_rule(m, t):
        return m.inventory[t] * m.backorder[t] == 0

    # Terminal conditions
    model.terminal_inv = pyo.Constraint(
        expr=model.inventory[5] >= params["terminal_min_inventory"]
    )
    model.terminal_back = pyo.Constraint(expr=model.backorder[5] == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}