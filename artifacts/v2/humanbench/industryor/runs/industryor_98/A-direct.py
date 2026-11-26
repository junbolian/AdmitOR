import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    profit_rate_1yr = params["profit_rate_1yr"]
    profit_rate_2yr = params["profit_rate_2yr"]

    # Decision variables (in yuan):
    # x1: amount invested in 1-year option at start of year 1
    # x2: amount invested in 2-year option at start of year 1
    # x3: amount invested in 1-year option at start of year 2
    # x4: amount invested in 1-year option at start of year 3
    # Cash carried forward each year: c1 (after year 1), c2 (after year 2), c3 (after year 3)
    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x3 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x4 = pyo.Var(domain=pyo.NonNegativeReals)
    model.c1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.c2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.c3 = pyo.Var(domain=pyo.NonNegativeReals)

    # Year 1: allocate initial capital between 1-year and 2-year options
    model.start_balance = pyo.Constraint(
        expr=model.x1 + model.x2 == initial_capital
    )

    # End of year 1: 1-year returns (principal + profit) plus uninvested cash
    # Note: all capital is invested, so cash after year 1 is 0 unless we treat
    # the returned amount as available. We model available funds pool c1.
    model.year1_balance = pyo.Constraint(
        expr=model.c1 == initial_capital - model.x1 - model.x2
        + model.x1 * (1.0 + profit_rate_1yr)
    )

    # Start of year 2: allocate available funds (c1) to 1-year option (x3)
    # The 2-year option from year 1 continues and has no cash flow yet.
    model.year2_start = pyo.Constraint(
        expr=model.x3 <= model.c1
    )

    # End of year 2: 1-year option from year 2 returns; 2-year option from
    # year 1 matures and returns principal + profit.
    model.year2_balance = pyo.Constraint(
        expr=model.c2 == model.c1 - model.x3
        + model.x3 * (1.0 + profit_rate_1yr)
        + model.x2 * (1.0 + profit_rate_2yr)
    )

    # Start of year 3: allocate available funds (c2) to 1-year option (x4)
    model.year3_start = pyo.Constraint(
        expr=model.x4 <= model.c2
    )

    # End of year 3: 1-year option from year 3 returns; remaining cash stays.
    model.year3_balance = pyo.Constraint(
        expr=model.c3 == model.c2 - model.x4
        + model.x4 * (1.0 + profit_rate_1yr)
    )

    # Maximize total money at end of year 3
    model.total_wealth = pyo.Expression(expr=model.c3)
    model.objective = pyo.Objective(expr=model.total_wealth, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.objective))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "solver failed"}