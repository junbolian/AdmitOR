import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    models_set = ['A', 'B']
    processes_set = ['I', 'II']

    model.x = pyo.Var(models_set, domain=pyo.NonNegativeReals)

    # Goal p1: total weekly profit at least target_profit
    model.profit_expr = pyo.Expression(
        expr=params["profit_A"] * model.x['A'] + params["profit_B"] * model.x['B']
    )

    # Goal p2: contractual minimum production levels
    model.min_prod_A = pyo.Constraint(expr=model.x['A'] >= params["min_units_A"])
    model.min_prod_B = pyo.Constraint(expr=model.x['B'] >= params["min_units_B"])

    # Goal p3: Process times should hit target hours (overtime possible, so lower bounds only)
    time_I_expr = params["time_I_A"] * model.x['A'] + params["time_I_B"] * model.x['B']
    time_II_expr = params["time_II_A"] * model.x['A'] + params["time_II_B"] * model.x['B']

    model.time_I_target = pyo.Constraint(expr=time_I_expr >= params["target_time_I"])
    model.time_II_target = pyo.Constraint(expr=time_II_expr >= params["target_time_II"])

    # Regular capacity constraints on Process I and Process II (without overtime)
    # Process I: weekly capacity, Process II: weekly capacity.
    model.cap_I = pyo.Constraint(expr=time_I_expr <= params["capacity_I"])
    model.cap_II = pyo.Constraint(expr=time_II_expr <= params["capacity_II"])

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}