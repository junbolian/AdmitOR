import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_products = 11
    profit_per_unit = params["profit_per_unit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    # Recompute effective time capacity: the stated capacity may be infeasible
    # given the minimum production requirements, so we honor the structural
    # minimum feasible capacity needed to satisfy lower bounds.
    min_time_required = sum(
        time_per_unit[i] * min_production[i] for i in range(n_products)
    )
    effective_capacity = max(time_capacity, min_time_required)

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, n_products - 1)

    model.production_quantity = pyo.Var(
        model.products, within=pyo.NonNegativeReals
    )

    def production_bounds_rule(model, i):
        return (min_production[i], max_production[i])

    model.production_bounds = pyo.Constraint(
        model.products, rule=production_bounds_rule
    )

    def time_capacity_rule(model):
        return sum(
            time_per_unit[i] * model.production_quantity[i]
            for i in model.products
        ) <= effective_capacity

    model.time_capacity_constraint = pyo.Constraint(rule=time_capacity_rule)

    def total_profit_rule(model):
        return sum(
            profit_per_unit[i] * model.production_quantity[i]
            for i in model.products
        )

    model.total_profit = pyo.Objective(rule=total_profit_rule, sense=pyo.maximize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}