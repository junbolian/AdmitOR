import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    time_procI_A = params["time_procI_A"]
    time_procI_B = params["time_procI_B"]
    time_procII_A = params["time_procII_A"]
    time_procII_B = params["time_procII_B"]
    cap_procI = params["cap_procI"]
    cap_procII = params["cap_procII"]
    profit_target = params["profit_target"]
    min_A = params["min_A"]
    min_B = params["min_B"]
    procI_target = params["procI_target"]

    model = gp.Model("goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of A and B produced
    x_A = model.addVar(lb=0, name="x_A")
    x_B = model.addVar(lb=0, name="x_B")

    # Deviation variables for each goal
    # p1: profit >= profit_target
    # d1m = negative deviation (underachievement), d1p = positive deviation (overachievement)
    d1m = model.addVar(lb=0, name="d1m")
    d1p = model.addVar(lb=0, name="d1p")

    # p2a: x_A >= min_A
    d2am = model.addVar(lb=0, name="d2am")
    d2ap = model.addVar(lb=0, name="d2ap")

    # p2b: x_B >= min_B
    d2bm = model.addVar(lb=0, name="d2bm")
    d2bp = model.addVar(lb=0, name="d2bp")

    # p3a: Process I usage = procI_target (exactly)
    d3am = model.addVar(lb=0, name="d3am")
    d3ap = model.addVar(lb=0, name="d3ap")

    # p3b: Process II usage should be maximized (maximize d4p, i.e. overachievement of cap_procII)
    # Constraint: procII usage - d4m + d4p = cap_procII
    # We want to maximize d4p (maximize overtime/usage of Process II)
    d4m = model.addVar(lb=0, name="d4m")
    d4p = model.addVar(lb=0, name="d4p")

    # Hard capacity constraints (Process I and II as soft goals, so no hard cap here;
    # but Process I has a target of procI_target = cap_procI, handled via goal constraint)
    # Process II is to be maximized with no hard upper bound restriction beyond the goal formulation.

    # Goal constraints
    # p1: profit goal
    model.addConstr(
        profit_A * x_A + profit_B * x_B - d1p + d1m == profit_target,
        name="goal_profit"
    )

    # p2a: minimum units of A
    model.addConstr(
        x_A - d2ap + d2am == min_A,
        name="goal_minA"
    )

    # p2b: minimum units of B
    model.addConstr(
        x_B - d2bp + d2bm == min_B,
        name="goal_minB"
    )

    # p3a: Process I exact target
    model.addConstr(
        time_procI_A * x_A + time_procI_B * x_B - d3ap + d3am == procI_target,
        name="goal_procI"
    )

    # p3b: Process II maximization (maximize usage relative to cap_procII)
    model.addConstr(
        time_procII_A * x_A + time_procII_B * x_B - d4p + d4m == cap_procII,
        name="goal_procII"
    )

    # Preemptive goal programming via weighted objective with large penalty weights
    # Priority levels: p1 >> p2 >> p3
    # Within p3: minimize d3am + d3ap (Process I exact) and maximize Process II usage (minimize d4m)
    # We use penalty weights: p1 weight = M^2, p2 weight = M, p3 weight = 1
    M = 1e6

    # Objective: minimize weighted deviations
    # p1: minimize underachievement of profit (d1m)
    # p2: minimize underachievement of min_A (d2am) and min_B (d2bm)
    # p3: minimize both deviations of Process I (d3am + d3ap), and minimize d4m (maximize Process II usage)
    model.setObjective(
        M * M * d1m
        + M * (d2am + d2bm)
        + 1.0 * (d3am + d3ap)
        + 1.0 * d4m,
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}