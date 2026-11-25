import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profits = [
        params["profit_supplier0"],
        params["profit_supplier1"],
        params["profit_supplier2"],
        params["profit_supplier3"],
    ]

    n_sup = 4
    n_reg = 5
    n_prod = 2

    suppliers = range(n_sup)
    regions = range(n_reg)
    products = range(n_prod)

    # demand may be a flat list; convert to nested list for safe indexing
    if isinstance(demand[0], (list, tuple)):
        demand_2d = [list(demand[r]) for r in regions]
    else:
        demand_2d = [
            [demand[r * n_prod + p] for p in products] for r in regions
        ]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(suppliers, regions, products, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(
            profits[s][r * n_prod + p] * model.x[s, r, p]
            for s in suppliers
            for r in regions
            for p in products
        ),
        sense=pyo.maximize,
    )

    def demand_rule(mdl, r, p):
        return sum(mdl.x[s, r, p] for s in suppliers) == demand_2d[r][p]

    model.demand_con = pyo.Constraint(regions, products, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}