# IR: {"sets":{"companies":[0,1],"markets":[0,1,2,3],"products":[0,1,2]},"params":{"demand":"4x3 market-major array, nested or flat","profit_company0":"4x3 market-major array, nested or flat","profit_company1":"4x3 market-major array, nested or flat"},"variables":{"supply[c,j,k]":"nonnegative continuous for each company c, market j, product k"},"constraints":["sum(c in companies) supply[c,j,k] == demand[j,k] for each market j and product k"],"objective":"maximize sum(c,j,k) profit_company[c][j,k] * supply[c,j,k]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = params["demand"]
    profit0_data = params["profit_company0"]
    profit1_data = params["profit_company1"]

    def matrix_entry(data, market, product):
        if len(data) == 12:
            return data[3 * market + product]
        return data[market][product]

    model = pyo.ConcreteModel()
    model.companies = pyo.RangeSet(0, 1)
    model.markets = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 2)

    model.demand = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda mdl, market, product: matrix_entry(
            demand_data, market, product
        ),
        within=pyo.Reals,
    )

    profit_data = {0: profit0_data, 1: profit1_data}
    model.unit_profit = pyo.Param(
        model.companies,
        model.markets,
        model.products,
        initialize=lambda mdl, company, market, product: matrix_entry(
            profit_data[company], market, product
        ),
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, market, product):
        return (
            sum(
                mdl.supply[company, market, product]
                for company in mdl.companies
            )
            == mdl.demand[market, product]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[company, market, product]
            * model.supply[company, market, product]
            for company in model.companies
            for market in model.markets
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}