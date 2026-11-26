import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    grains = ['1', '2', '3']
    nutrients = ['A', 'B', 'C', 'D']

    cost = {
        '1': params["cost_grain1"],
        '2': params["cost_grain2"],
        '3': params["cost_grain3"],
    }
    nutrient = {
        ('A', '1'): params["nutrient_A_grain1"],
        ('A', '2'): params["nutrient_A_grain2"],
        ('A', '3'): params["nutrient_A_grain3"],
        ('B', '1'): params["nutrient_B_grain1"],
        ('B', '2'): params["nutrient_B_grain2"],
        ('B', '3'): params["nutrient_B_grain3"],
        ('C', '1'): params["nutrient_C_grain1"],
        ('C', '2'): params["nutrient_C_grain2"],
        ('C', '3'): params["nutrient_C_grain3"],
        ('D', '1'): params["nutrient_D_grain1"],
        ('D', '2'): params["nutrient_D_grain2"],
        ('D', '3'): params["nutrient_D_grain3"],
    }
    req = {
        'A': params["req_A"],
        'B': params["req_B"],
        'C': params["req_C"],
        'D': params["req_D"],
    }

    model.x = pyo.Var(grains, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[g] * model.x[g] for g in grains),
        sense=pyo.minimize,
    )

    model.nutr_con = pyo.Constraint(
        nutrients,
        rule=lambda m, n: sum(nutrient[(n, g)] * m.x[g] for g in grains) >= req[n],
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except Exception:
        return {'objective': None, 'status': 'infeasible or failed'}