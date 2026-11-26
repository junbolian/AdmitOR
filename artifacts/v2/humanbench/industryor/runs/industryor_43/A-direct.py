import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    workers_initial = params["workers_initial"]
    prod_per_worker = params["prod_per_worker"]
    demand = params["demand"]
    overtime_max_per_worker = params["overtime_max_per_worker"]
    overtime_unit_cost = params["overtime_unit_cost"]
    holding_cost = params["holding_cost"]
    max_workforce_change = params["max_workforce_change"]
    hiring_cost = params["hiring_cost"]
    layoff_cost = params["layoff_cost"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    months = list(range(1, 7))
    model = pyo.ConcreteModel()
    model.months = pyo.Set(initialize=months)

    model.workers = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.hired = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.laidoff = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def workforce_balance_rule(m, t):
        if t == 1:
            return m.workers[t] == workers_initial + m.hired[t] - m.laidoff[t]
        return m.workers[t] == m.workers[t - 1] + m.hired[t] - m.laidoff[t]

    model.workforce_balance = pyo.Constraint(model.months, rule=workforce_balance_rule)

    def change_limit_rule(m, t):
        return m.hired[t] + m.laidoff[t] <= max_workforce_change

    model.change_limit = pyo.Constraint(model.months, rule=change_limit_rule)

    def overtime_limit_rule(m, t):
        return m.overtime[t] <= overtime_max_per_worker * m.workers[t]

    model.overtime_limit = pyo.Constraint(model.months, rule=overtime_limit_rule)

    def inventory_balance_rule(m, t):
        regular = prod_per_worker * m.workers[t]
        if t == 1:
            return m.inventory[t] == initial_inventory + regular + m.overtime[t] - demand[t - 1]
        return m.inventory[t] == m.inventory[t - 1] + regular + m.overtime[t] - demand[t - 1]

    model.inventory_balance = pyo.Constraint(model.months, rule=inventory_balance_rule)

    model.final_inventory_req = pyo.Constraint(
        expr=model.inventory[6] == final_inventory
    )

    def obj_rule(m):
        total_revenue = sum(demand[t - 1] for t in months)
        return (
            total_revenue
            - sum(overtime_unit_cost * m.overtime[t] for t in months)
            - sum(holding_cost * m.inventory[t] for t in months)
            - sum(hiring_cost * m.hired[t] for t in months)
            - sum(layoff_cost * m.laidoff[t] for t in months)
        )

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}