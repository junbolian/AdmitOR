import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: barrels of milk allocated to each product
    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)  # barrels -> A1
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)  # barrels -> A2

    # Objective: maximize total profit
    model.profit = pyo.Objective(
        expr=params["profit_A1"] * params["A1_per_barrel"] * model.x1
        + params["profit_A2"] * params["A2_per_barrel"] * model.x2,
        sense=pyo.maximize,
    )

    # Milk supply constraint (barrels)
    model.milk = pyo.Constraint(
        expr=model.x1 + model.x2 <= params["milk_supply"]
    )

    # Labor hours constraint
    model.labor = pyo.Constraint(
        expr=params["hours_per_barrel_A1"] * model.x1
        + params["hours_per_barrel_A2"] * model.x2
        <= params["labor_hours"]
    )

    # Type A equipment capacity for A1 (kg/day)
    model.capA1 = pyo.Constraint(
        expr=params["A1_per_barrel"] * model.x1 <= params["A1_capacity"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}