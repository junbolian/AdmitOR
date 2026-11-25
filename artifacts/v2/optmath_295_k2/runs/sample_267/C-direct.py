import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost_type0 = params["fixed_cost_type0"]
    fixed_cost_type1 = params["fixed_cost_type1"]
    var_cost_type0 = params["var_cost_type0"]
    var_cost_type1 = params["var_cost_type1"]
    start_cost_type0 = params["start_cost_type0"]
    start_cost_type1 = params["start_cost_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    capac_req = params["capac_req"]
    max_operational_type0 = params["max_operational_type0"]
    max_operational_type1 = params["max_operational_type1"]
    max_start_period0_type0 = params["max_start_period0_type0"]
    max_start_period0_type1 = params["max_start_period0_type1"]

    T = 5  # number of periods

    model = gp.Model("unit_commitment")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # n0[t]: number of Type 0 generators operational in period t
    # n1[t]: number of Type 1 generators operational in period t
    # p0[t]: total power output of Type 0 generators in period t
    # p1[t]: total power output of Type 1 generators in period t
    # s0[t]: number of Type 0 generators started in period t
    # s1[t]: number of Type 1 generators started in period t

    n0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="n0")
    n1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="n1")
    p0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="p0")
    p1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="p1")
    s0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="s0")
    s1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="s1")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            fixed_cost_type0 * n0[t] +
            fixed_cost_type1 * n1[t] +
            var_cost_type0 * p0[t] +
            var_cost_type1 * p1[t] +
            start_cost_type0 * s0[t] +
            start_cost_type1 * s1[t]
            for t in range(T)
        ),
        GRB.MINIMIZE
    )

    for t in range(T):
        # Demand constraint
        model.addConstr(p0[t] + p1[t] >= demand[t], name=f"demand_{t}")

        # Capacity requirement constraint
        model.addConstr(
            max_output_type0 * n0[t] + max_output_type1 * n1[t] >= capac_req[t],
            name=f"capac_req_{t}"
        )

        # Output bounds for Type 0
        model.addConstr(p0[t] >= min_output_type0 * n0[t], name=f"min_p0_{t}")
        model.addConstr(p0[t] <= max_output_type0 * n0[t], name=f"max_p0_{t}")

        # Output bounds for Type 1
        model.addConstr(p1[t] >= min_output_type1 * n1[t], name=f"min_p1_{t}")
        model.addConstr(p1[t] <= max_output_type1 * n1[t], name=f"max_p1_{t}")

        # Max operational constraints
        model.addConstr(n0[t] <= max_operational_type0, name=f"max_n0_{t}")
        model.addConstr(n1[t] <= max_operational_type1, name=f"max_n1_{t}")

    # Startup constraints for Period 0
    model.addConstr(s0[0] <= max_start_period0_type0, name="max_start_p0_type0")
    model.addConstr(s1[0] <= max_start_period0_type1, name="max_start_p0_type1")

    # Operational continuity: n[t] <= n[t-1] + s[t]
    # Startup constraints for subsequent periods: s[t] <= n[t-1]
    for t in range(1, T):
        model.addConstr(n0[t] <= n0[t-1] + s0[t], name=f"n0_continuity_{t}")
        model.addConstr(n1[t] <= n1[t-1] + s1[t], name=f"n1_continuity_{t}")
        model.addConstr(s0[t] <= n0[t-1], name=f"s0_limit_{t}")
        model.addConstr(s1[t] <= n1[t-1], name=f"s1_limit_{t}")

    # For period 0: n[0] <= s[0] (no generators were operational before)
    model.addConstr(n0[0] <= s0[0], name="n0_period0_continuity")
    model.addConstr(n1[0] <= s1[0], name="n1_period0_continuity")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}