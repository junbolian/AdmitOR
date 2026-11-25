# IR: {"sets":{"S":[0,1,2,3],"R":[0,1,2,3,4],"P":[0,1]},"params":{"demand":"d[r,p], supplied as 10 row-major entries or a 5x2 array","profit_supplier0":"c[0,r,p], 10 row-major entries","profit_supplier1":"c[1,r,p], 10 row-major entries","profit_supplier2":"c[2,r,p], 10 row-major entries","profit_supplier3":"c[3,r,p], 10 row-major entries"},"variables":{"x[s,r,p]":"nonnegative continuous"},"constraints":["sum(x[s,r,p] for s in S) == d[r,p] for each r,p"],"objective":"maximize sum(c[s,r,p]*x[s,r,p] for s,r,p)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_input = params["demand"]
    supplier_profits = [
        params["profit_supplier0"],
        params["profit_supplier1"],
        params["profit_supplier2"],
        params["profit_supplier3"],
    ]

    if len(demand_input) == 10:
        demand_data = {
            (region, product): demand_input[2 * region + product]
            for region in range(5)
            for product in range(2)
        }
    elif len(demand_input) == 5:
        if any(len(row) != 2 for row in demand_input):
            raise ValueError("Nested demand must contain five rows of two entries.")
        demand_data = {
            (region, product): demand_input[region][product]
            for region in range(5)
            for product in range(2)
        }
    else:
        raise ValueError("Demand must contain ten entries or five rows of two.")

    if any(len(values) != 10 for values in supplier_profits):
        raise ValueError("Each supplier profit array must contain ten entries.")

    profit_data = {
        (supplier, region, product):
            supplier_profits[supplier][2 * region + product]
        for supplier in range(4)
        for region in range(5)
        for product in range(2)
    }

    model = pyo.ConcreteModel()
    model.suppliers = pyo.RangeSet(0, 3)
    model.regions = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.demand = pyo.Param(
        model.regions,
        model.products,
        initialize=demand_data,
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.suppliers,
        model.regions,
        model.products,
        initialize=profit_data,
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.suppliers,
        model.regions,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, region, product):
        return (
            sum(
                instance.supply[supplier, region, product]
                for supplier in instance.suppliers
            )
            == instance.demand[region, product]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.regions,
        model.products,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[supplier, region, product]
            * model.supply[supplier, region, product]
            for supplier in model.suppliers
            for region in model.regions
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    # APPSI may raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval below is the sole test for success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}