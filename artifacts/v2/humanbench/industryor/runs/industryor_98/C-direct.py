import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_capital = params["initial_capital"]
    profit_rate_1yr = params["profit_rate_1yr"]
    profit_rate_2yr = params["profit_rate_2yr"]

    # Return per yuan invested (principal + profit)
    return_1yr = 1 + profit_rate_1yr   # after 1 year
    return_2yr = 1 + profit_rate_2yr   # after 2 years

    # Decision variables:
    # x1: amount invested in 1-year option at start of year 1
    # x2: amount invested in 2-year option at start of year 1 (runs years 1-2)
    # x3: amount invested in 1-year option at start of year 2 (from x1 returns)
    # x4: amount invested in 1-year option at start of year 3
    #     (from x3 returns + x2 returns at end of year 2)
    # x5: amount invested in 2-year option at start of year 3 (runs years 3-4,
    #     but we only count what's available; however the 2-yr option must be
    #     a multiple of 2 years, so it won't mature by end of year 3 —
    #     the investor gets back principal+profit only at end of year 4,
    #     so investing in the 2-yr option at year 3 does NOT contribute to
    #     end-of-year-3 wealth. We exclude it.)
    #
    # Timeline:
    #   Year 0 (start): invest x1 (1-yr) + x2 (2-yr) = initial_capital
    #   End of year 1:  x1 matures -> return_1yr * x1; invest x3 (1-yr)
    #                   x3 <= return_1yr * x1
    #   End of year 2:  x3 matures -> return_1yr * x3
    #                   x2 matures -> return_2yr * x2
    #                   invest x4 (1-yr)
    #                   x4 <= return_1yr * x3 + return_2yr * x2
    #   End of year 3:  x4 matures -> return_1yr * x4
    #                   Total wealth = return_1yr * x4 + (uninvested cash at each stage)
    #
    # To maximize end-of-year-3 wealth we should invest all available cash,
    # but we model it properly with slack (uninvested) variables to keep LP general.

    model = gp.Model("investment")
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(lb=0, name="x1")  # 1-yr investment at t=0
    x2 = model.addVar(lb=0, name="x2")  # 2-yr investment at t=0
    x3 = model.addVar(lb=0, name="x3")  # 1-yr investment at t=1
    x4 = model.addVar(lb=0, name="x4")  # 1-yr investment at t=2

    # Slack (idle cash) at each period
    s0 = model.addVar(lb=0, name="s0")  # idle at t=0
    s1 = model.addVar(lb=0, name="s1")  # idle at t=1 (not reinvested)
    s2 = model.addVar(lb=0, name="s2")  # idle at t=2 (not reinvested)

    # t=0 budget constraint
    model.addConstr(x1 + x2 + s0 == initial_capital, name="budget_t0")

    # t=1: proceeds from x1 and idle s0 can be reinvested as x3 or kept idle
    model.addConstr(x3 + s1 == return_1yr * x1 + s0, name="budget_t1")

    # t=2: proceeds from x3, x2, and idle s1 can be reinvested as x4 or kept idle
    model.addConstr(x4 + s2 == return_1yr * x3 + return_2yr * x2 + s1, name="budget_t2")

    # Objective: total wealth at end of year 3
    # = proceeds from x4 (1-yr at t=2) + idle cash s2
    total_wealth = return_1yr * x4 + s2
    model.setObjective(total_wealth, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        # Profit earned = total wealth minus initial capital
        return {"objective": float(model.ObjVal - initial_capital), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}