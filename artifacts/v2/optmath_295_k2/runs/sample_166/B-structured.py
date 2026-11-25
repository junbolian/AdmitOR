# IR: {"sets":{"S":[0,1,2,3],"R":[0,1,2,3,4],"P":[0,1]},"params":{"demand":"d[r,p], supplied as a 5x2 array or flat row-major array of length 10","profit_supplier0":"flat row-major array of length 10","profit_supplier1":"flat row-major array of length 10","profit_supplier2":"flat row-major array of length 10","profit_supplier3":"flat row-major array of length 10"},"variables":{"x[s,r,p]":"nonnegative continuous"},"constraints":["For every r,p: sum(s in S, x[s,r,p]) = d[r,p]"],"objective":"maximize sum(s in S, r in R, p in P, profit_supplier_s[2*r+p] * x[s,r,p])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = params["demand"]
    profit_data = (
        params["profit_supplier0"],
        params["profit_supplier1"],
        params["profit_supplier2"],
        params["profit_supplier3"],
    )

    if len(demand_data) == 5:
        if any(len(row) != 2 for row in demand_data):
            raise ValueError("Nested demand must have five rows and two columns.")
        demand_values = {
            (region, product): demand_data[region][product]
            for region in range(5)
            for product in range(2)
        }
    elif len(demand_data) == 10:
        demand_values = {
            (region, product): demand_data[2 * region + product]
            for region in range(5)
            for product in range(2)
        }
    else:
        raise ValueError("Demand must be a 5x2 array or a flat array of length 10.")

    if any(len(supplier_data) != 10 for supplier_data in profit_data):
        raise ValueError("Each supplier profit array must have length 10.")

    model = pyo.ConcreteModel()
    model.suppliers = pyo.RangeSet(0, 3)
    model.regions = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.demand = pyo.Param(
        model.regions,
        model.products,
        initialize=demand_values,
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.suppliers,
        model.regions,
        model.products,
        initialize={
            (supplier, region, product): profit_data[supplier][2 * region + product]
            for supplier in range(4)
            for region in range(5)
            for product in range(2)
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.suppliers,
        model.regions,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, region, product):
        return (
            sum(
                instance.x[supplier, region, product]
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
            * model.x[supplier, region, product]
            for supplier in model.suppliers
            for region in model.regions
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}