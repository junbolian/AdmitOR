import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit_margin = params["profit_margin"]

    num_suppliers = len(profit_margin)
    num_products = len(profit_margin[0])
    num_regions = len(profit_margin[0][0])

    demand_map = {}
    for p in range(num_products):
        for r in range(num_regions):
            demand_map[(p, r)] = demand[p * num_regions + r]

    model = pyo.ConcreteModel()

    model.suppliers = pyo.RangeSet(0, num_suppliers - 1)
    model.products = pyo.RangeSet(0, num_products - 1)
    model.regions = pyo.RangeSet(0, num_regions - 1)

    model.qty = pyo.Var(
        model.suppliers, model.products, model.regions,
        domain=pyo.NonNegativeReals,
    )

    def profit_rule(model):
        return sum(
            profit_margin[s][p][r] * model.qty[s, p, r]
            for s in model.suppliers
            for p in model.products
            for r in model.regions
        )

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def demand_rule(model, p, r):
        return sum(model.qty[s, p, r] for s in model.suppliers) == demand_map[(p, r)]

    model.demand_con = pyo.Constraint(model.products, model.regions, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_profit))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}