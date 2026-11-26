import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    machine_minutes_X = params["machine_minutes_X"]
    craftsman_minutes_X = params["craftsman_minutes_X"]
    machine_minutes_Y = params["machine_minutes_Y"]
    craftsman_minutes_Y = params["craftsman_minutes_Y"]
    machine_hours_capacity = params["machine_hours_capacity"]
    craftsman_hours_capacity = params["craftsman_hours_capacity"]
    machine_cost_per_hour = params["machine_cost_per_hour"]
    craftsman_cost_per_hour = params["craftsman_cost_per_hour"]
    revenue_X = params["revenue_X"]
    revenue_Y = params["revenue_Y"]
    contract_min_X = params["contract_min_X"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Machine capacity (minutes)
    model.machine_cap = pyo.Constraint(
        expr=machine_minutes_X * model.x + machine_minutes_Y * model.y
        <= machine_hours_capacity * 60
    )

    # Craftsman capacity (minutes)
    model.craftsman_cap = pyo.Constraint(
        expr=craftsman_minutes_X * model.x + craftsman_minutes_Y * model.y
        <= craftsman_hours_capacity * 60
    )

    # Contract minimum for X
    model.contract = pyo.Constraint(expr=model.x >= contract_min_X)

    # Objective: maximize profit (revenue minus resource costs actually incurred)
    # Costs depend on resources used (idle time free), so express per-unit cost.
    machine_cost_X = (machine_minutes_X / 60.0) * machine_cost_per_hour
    machine_cost_Y = (machine_minutes_Y / 60.0) * machine_cost_per_hour
    craftsman_cost_X = (craftsman_minutes_X / 60.0) * craftsman_cost_per_hour
    craftsman_cost_Y = (craftsman_minutes_Y / 60.0) * craftsman_cost_per_hour

    profit_X = revenue_X - machine_cost_X - craftsman_cost_X
    profit_Y = revenue_Y - machine_cost_Y - craftsman_cost_Y

    model.total_profit = pyo.Expression(
        expr=profit_X * model.x + profit_Y * model.y
    )
    model.obj = pyo.Objective(expr=model.total_profit, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}