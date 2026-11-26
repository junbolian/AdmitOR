import gurobipy as gp
from gurobipy import GRB

def solve(params):
    C = params["total_capital"]
    r1 = params["return_rate_option1"]   # total return per yuan, 1-year option
    r2 = params["return_rate_option2"]   # total return per yuan, 2-year option

    # Time points: start of year 1 (t=0), start of year 2 (t=1), start of year 3 (t=2)
    # x1[t]: yuan in 1-year option at start of year t+1 (matures one year later)
    # x2[t]: yuan in 2-year option at start of year t+1 (matures two years later)
    model = gp.Model("investment")
    model.Params.OutputFlag = 0

    x1 = {t: model.addVar(lb=0, ub=GRB.INFINITY, name=f"x1_{t}") for t in range(3)}
    x2 = {t: model.addVar(lb=0, ub=GRB.INFINITY, name=f"x2_{t}") for t in range(2)}
    # idle cash carried from one year-start to the next
    s = {t: model.addVar(lb=0, ub=GRB.INFINITY, name=f"slack_{t}") for t in range(3)}

    # Cash-flow balance at each year-start
    # t=0: initial capital is split between both options and idle cash
    model.addConstr(x1[0] + x2[0] + s[0] == C, "cash_t0")

    # t=1: available = idle from t=0 (nothing has matured yet)
    model.addConstr(x1[1] + x2[1] + s[1] == s[0], "cash_t1")

    # t=2: available = idle from t=1 + maturity of x1[0]
    model.addConstr(x1[2] + s[2] == s[1] + r1 * x1[0], "cash_t2")

    # Final wealth at end of year 3:
    # idle cash + maturities: x1[1] (end yr 2), x2[0] (end yr 2, held as cash),
    # x1[2] and x2[1] mature exactly at end of year 3.
    final_wealth = (
        s[2]
        + r1 * x1[1]
        + r2 * x2[0]
        + r1 * x1[2]
        + r2 * x2[1]
    )
    model.setObjective(final_wealth, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed: status {model.Status}"}