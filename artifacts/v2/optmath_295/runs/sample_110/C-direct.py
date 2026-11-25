import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost_type0 = params["base_cost_type0"]
    base_cost_type1 = params["base_cost_type1"]
    power_cost_type0 = params["power_cost_type0"]
    power_cost_type1 = params["power_cost_type1"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    reserve_margin = params["reserve_margin"]
    max_active_per_type = params["max_active_per_type"]
    max_startups_first_period_type0 = params["max_startups_first_period_type0"]
    max_startups_first_period_type1 = params["max_startups_first_period_type1"]

    T = 5  # periods 0..4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # n0[t]: number of active Type 0 generators in period t (integer)
    # n1[t]: number of active Type 1 generators in period t (integer)
    # p0[t]: total power output from Type 0 generators in period t (continuous)
    # p1[t]: total power output from Type 1 generators in period t (continuous)
    # s0[t]: number of Type 0 generator startups in period t (integer)
    # s1[t]: number of Type 1 generator startups in period t (integer)

    n0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, ub=max_active_per_type, name="n0")
    n1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, ub=max_active_per_type, name="n1")
    p0 = model.addVars(T, vtype=GRB.CONTINUOUS, lb=0.0, name="p0")
    p1 = model.addVars(T, vtype=GRB.CONTINUOUS, lb=0.0, name="p1")
    s0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="s0")
    s1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="s1")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            base_cost_type0 * n0[t] + base_cost_type1 * n1[t]
            + power_cost_type0 * p0[t] + power_cost_type1 * p1[t]
            + startup_cost_type0 * s0[t] + startup_cost_type1 * s1[t]
            for t in range(T)
        ),
        GRB.MINIMIZE
    )

    for t in range(T):
        d = demand[t]

        # Meet demand
        model.addConstr(p0[t] + p1[t] >= d, name=f"demand_{t}")

        # Reserve margin: total max capacity >= (1 + reserve_margin) * demand
        model.addConstr(
            max_output_type0 * n0[t] + max_output_type1 * n1[t] >= (1.0 + reserve_margin) * d,
            name=f"reserve_{t}"
        )

        # Output bounds: active generators produce within [min, max]
        model.addConstr(p0[t] >= min_output_type0 * n0[t], name=f"p0_min_{t}")
        model.addConstr(p0[t] <= max_output_type0 * n0[t], name=f"p0_max_{t}")
        model.addConstr(p1[t] >= min_output_type1 * n1[t], name=f"p1_min_{t}")
        model.addConstr(p1[t] <= max_output_type1 * n1[t], name=f"p1_max_{t}")

    # Startup constraints for period 0
    model.addConstr(s0[0] <= max_startups_first_period_type0, name="startup0_t0")
    model.addConstr(s1[0] <= max_startups_first_period_type1, name="startup1_t0")

    # In period 0: active generators <= startups (no prior period)
    model.addConstr(n0[0] <= s0[0], name="active0_t0")
    model.addConstr(n1[0] <= s1[0], name="active1_t0")

    # Startup and continuity constraints for periods 1..4
    for t in range(1, T):
        # Active generators can't exceed previous active + new startups
        model.addConstr(n0[t] <= n0[t-1] + s0[t], name=f"active0_cont_{t}")
        model.addConstr(n1[t] <= n1[t-1] + s1[t], name=f"active1_cont_{t}")

        # Startups bounded by increase in active generators
        model.addConstr(s0[t] >= n0[t] - n0[t-1], name=f"startup0_lb_{t}")
        model.addConstr(s1[t] >= n1[t] - n1[t-1], name=f"startup1_lb_{t}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}