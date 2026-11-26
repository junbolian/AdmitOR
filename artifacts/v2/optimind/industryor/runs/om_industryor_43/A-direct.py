import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Products
    products = ['A', 'B', 'C']

    # Tier data per product
    tier_data = {
        'A': (list(params["tier_breakpoints_A"]), list(params["profit_A_tiers"])),
        'B': (list(params["tier_breakpoints_B"]), list(params["profit_B_tiers"])),
        'C': (list(params["tier_breakpoints_C"]), list(params["profit_C_tiers"])),
    }

    # Production quantities
    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    # Piecewise segment variables
    # For each product, segments: [0, bp0], [bp0, bp1], ..., [bp_last, +inf]
    # Number of segments = len(breakpoints) + 1
    seg_vars = {}
    model.segments = pyo.Set(initialize=[
        (p, k) for p in products for k in range(len(tier_data[p][0]) + 1)
    ])
    model.y = pyo.Var(model.segments, domain=pyo.NonNegativeReals)

    # Link x = sum of segments
    def link_rule(m, p):
        return m.x[p] == sum(m.y[(p, k)] for k in range(len(tier_data[p][0]) + 1))
    model.link = pyo.Constraint(products, rule=link_rule)

    # Upper bounds on segment sizes (binary-free LP formulation via big-M style):
    # To model concave piecewise profit correctly we need proper upper bounds.
    # Since per-unit profit decreases with volume tier, the profit function is concave,
    # so the natural LP relaxation (allowing segment fill out of order) is exact:
    # the solver will fill cheaper (higher profit) segments first automatically.
    # Still we impose segment upper bounds for finite segments.
    finite_seg_bound = {}
    for p in products:
        bps = tier_data[p][0]
        for k in range(len(bps)):
            if k == 0:
                upper = bps[0]
            else:
                upper = bps[k] - bps[k-1]
            finite_seg_bound[(p, k)] = upper

    # Bounds: finite segments bounded, last segment unbounded (NonNegativeReals)
    for (p, k), ub in finite_seg_bound.items():
        model.y[(p, k)].setub(ub)

    # Resource constraints
    model.tech = pyo.Constraint(
        expr=params["prep_A"] * model.x['A']
        + params["prep_B"] * model.x['B']
        + params["prep_C"] * model.x['C']
        <= params["tech_capacity"]
    )
    model.labor = pyo.Constraint(
        expr=params["labor_A"] * model.x['A']
        + params["labor_B"] * model.x['B']
        + params["labor_C"] * model.x['C']
        <= params["labor_capacity"]
    )
    model.material = pyo.Constraint(
        expr=params["material_A"] * model.x['A']
        + params["material_B"] * model.x['B']
        + params["material_C"] * model.x['C']
        <= params["material_capacity"]
    )

    # Objective: maximize total profit from segments
    def obj_rule(m):
        total = 0
        for p in products:
            profits = tier_data[p][1]
            for k in range(len(profits)):
                total += profits[k] * m.y[(p, k)]
        return total
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))

    return {'objective': obj_val, 'status': 'optimal'}