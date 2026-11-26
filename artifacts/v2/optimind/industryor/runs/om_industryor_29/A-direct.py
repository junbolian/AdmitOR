import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _as_map(value, products):
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        return {p: value[i] for i, p in enumerate(products)}
    return {p: value for p in products}


def solve(params):
    model = pyo.ConcreteModel()

    products = ['I', 'II', 'III']
    routes = {
        'I': [('A1', 'B1'), ('A1', 'B2'), ('A1', 'B3'),
              ('A2', 'B1'), ('A2', 'B2'), ('A2', 'B3')],
        'II': [('A1', 'B1'), ('A2', 'B1')],
        'III': [('A2', 'B2')],
    }

    a_hours = {
        ('A1', 'I'): params['A1_hours'],
        ('A1', 'II'): params['A1_hours_II'],
        ('A2', 'I'): params['A2_hours_I'],
        ('A2', 'II'): params['A2_hours_II'],
        ('A2', 'III'): params['A2_hours_III'],
    }
    b_hours = {
        ('B1', 'I'): params['B1_hours_I'],
        ('B1', 'II'): params['B1_hours_II'],
        ('B2', 'I'): params['B2_hours_I'],
        ('B2', 'III'): params['B2_hours_III'],
        ('B3', 'I'): params['B3_hours_I'],
    }

    capacities = {
        'A1': params['capacity_A1'],
        'A2': params['capacity_A2'],
        'B1': params['capacity_B1'],
        'B2': params['capacity_B2'],
        'B3': params['capacity_B3'],
    }

    proc_cost = {
        'A1': params['proc_cost_A1'],
        'A2': params['proc_cost_A2'],
        'B1': params['proc_cost_B1'],
        'B2': params['proc_cost_B2'],
        'B3': params['proc_cost_B3'],
    }

    unit_price = _as_map(params['unit_price'], products)
    raw_cost = _as_map(params['raw_material_cost'], products)

    route_index = [(p, a, b) for p in products for (a, b) in routes[p]]
    model.X = pyo.Var(route_index, domain=pyo.NonNegativeReals)

    revenue_expr = sum(unit_price[p] * model.X[p, a, b]
                       for (p, a, b) in route_index)
    raw_expr = sum(raw_cost[p] * model.X[p, a, b]
                   for (p, a, b) in route_index)
    proc_expr = sum((proc_cost[a] * a_hours[(a, p)] +
                     proc_cost[b] * b_hours[(b, p)]) * model.X[p, a, b]
                    for (p, a, b) in route_index)

    model.profit = pyo.Expression(expr=revenue_expr - raw_expr - proc_expr)
    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    def cap_A_rule(mdl, mach):
        return sum(a_hours[(mach, p)] * mdl.X[p, a, b]
                   for (p, a, b) in route_index if a == mach) <= capacities[mach]
    model.cap_A = pyo.Constraint(['A1', 'A2'], rule=cap_A_rule)

    def cap_B_rule(mdl, mach):
        return sum(b_hours[(mach, p)] * mdl.X[p, a, b]
                   for (p, a, b) in route_index if b == mach) <= capacities[mach]
    model.cap_B = pyo.Constraint(['B1', 'B2', 'B3'], rule=cap_B_rule)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}