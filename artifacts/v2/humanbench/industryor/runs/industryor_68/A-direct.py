import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 6
    months = list(range(1, T + 1))

    demand = params["demand"]
    raw_material_cost = params["raw_material_cost"]
    labor_hours_per_unit = params["labor_hours_per_unit"]
    unit_price = params["unit_price"]
    initial_workers = params["initial_workers"]
    initial_inventory = params["initial_inventory"]
    normal_wage = params["normal_wage"]
    normal_hours_per_day = params["normal_hours_per_day"]
    overtime_wage = params["overtime_wage"]
    working_days_per_month = params["working_days_per_month"]
    max_overtime_hours_per_worker = params["max_overtime_hours_per_worker"]
    outsourcing_cost = params["outsourcing_cost"]
    inventory_cost = params["inventory_cost"]
    stockout_cost = params["stockout_cost"]
    hiring_cost = params["hiring_cost"]
    firing_cost = params["firing_cost"]
    min_final_inventory = params["min_final_inventory"]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=months)

    # Decision variables
    model.produce = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.outsource = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.stockout = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.workers = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.hire = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.fire = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    # Inventory balance
    def inventory_balance_rule(md, t):
        prev_inv = initial_inventory if t == 1 else md.inventory[t - 1]
        prev_stock = 0 if t == 1 else md.stockout[t - 1]
        return (prev_inv + md.produce[t] + md.outsource[t] - md.stockout[t]
                == demand[t - 1] + md.inventory[t])

    model.inventory_balance = pyo.Constraint(model.T, rule=inventory_balance_rule)

    # End inventory requirement
    def final_inv_rule(md):
        return md.inventory[T] >= min_final_inventory

    model.final_inv = pyo.Constraint(rule=final_inv_rule)

    # Workforce balance
    def workforce_balance_rule(md, t):
        prev = initial_workers if t == 1 else md.workers[t - 1]
        return md.workers[t] == prev + md.hire[t] - md.fire[t]

    model.workforce_balance = pyo.Constraint(model.T, rule=workforce_balance_rule)

    # Production capacity (labor hours)
    def capacity_rule(md, t):
        regular_hours = (md.workers[t] * normal_hours_per_day
                         * working_days_per_month)
        overtime_cap = md.workers[t] * max_overtime_hours_per_worker
        return (labor_hours_per_unit * md.produce[t]
                <= regular_hours + md.overtime[t])

    model.capacity = pyo.Constraint(model.T, rule=capacity_rule)

    # Overtime limit
    def overtime_limit_rule(md, t):
        return md.overtime[t] <= md.workers[t] * max_overtime_hours_per_worker

    model.overtime_limit = pyo.Constraint(model.T, rule=overtime_limit_rule)

    # Objective: maximize net profit
    def revenue_rule(md):
        return sum(unit_price * (demand[t - 1] - md.stockout[t])
                   for t in md.T)

    def cost_rule(md):
        raw = sum(raw_material_cost * md.produce[t] for t in md.T)
        outs = sum(outsourcing_cost * md.outsource[t] for t in md.T)
        inv = sum(inventory_cost * md.inventory[t] for t in md.T)
        stock = sum(stockout_cost * md.stockout[t] for t in md.T)
        normal = sum(normal_wage * normal_hours_per_day
                     * working_days_per_month * md.workers[t]
                     for t in md.T)
        overtime_c = sum(overtime_wage * md.overtime[t] for t in md.T)
        hire_c = sum(hiring_cost * md.hire[t] for t in md.T)
        fire_c = sum(firing_cost * md.fire[t] for t in md.T)
        return (raw + outs + inv + stock + normal + overtime_c
                + hire_c + fire_c)

    model.revenue = pyo.Expression(rule=revenue_rule)
    model.total_cost = pyo.Expression(rule=cost_rule)
    model.profit = pyo.Objective(
        expr=model.revenue - model.total_cost, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}