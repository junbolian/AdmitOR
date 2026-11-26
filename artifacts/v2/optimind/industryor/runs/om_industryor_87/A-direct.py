import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    hours_available = params["hours_available"]
    hours_per_A = params["hours_per_A"]
    hours_per_B = params["hours_per_B"]
    demand_ratio_B_to_A = params["demand_ratio_B_to_A"]
    space_per_A = params["space_per_A"]
    space_per_B = params["space_per_B"]
    storage_capacity = params["storage_capacity"]

    model = pyo.ConcreteModel()

    # Integer decision variables: units of A and B (whole units)
    model.x_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x_B = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Objective: maximize total profit
    def obj_rule(mdl):
        return profit_A * mdl.x_A + profit_B * mdl.x_B

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Production hours constraint
    def hours_rule(mdl):
        return hours_per_A * mdl.x_A + hours_per_B * mdl.x_B <= hours_available

    model.hours_constraint = pyo.Constraint(rule=hours_rule)

    # Demand constraint: B must be at least ratio * A  =>  B - ratio*A >= 0
    def demand_rule(mdl):
        return mdl.x_B - demand_ratio_B_to_A * mdl.x_A >= 0

    model.demand_constraint = pyo.Constraint(rule=demand_rule)

    # Storage capacity constraint
    def storage_rule(mdl):
        return space_per_A * mdl.x_A + space_per_B * mdl.x_B <= storage_capacity

    model.storage_constraint = pyo.Constraint(rule=storage_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_profit))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or could not retrieve objective"}