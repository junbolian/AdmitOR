import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost = params["base_cost_per_generator_per_period"]
    power_cost = params["power_cost_per_mw"]
    startup_cost_t0 = params["startup_cost_type0"]
    startup_cost_t1 = params["startup_cost_type1"]
    demand = params["demand_per_period"]
    capacity_margin_demand = params["capacity_margin_demand"]
    min_out_t0 = params["min_output_type0"]
    max_out_t0 = params["max_output_type0"]
    min_out_t1 = params["min_output_type1"]
    max_out_t1 = params["max_output_type1"]
    max_gen = params["max_generators_per_type_per_period"]
    offset_t0_p0 = params["type0_period0_operating_limit_offset"]
    offset_t1_p0 = params["type1_period0_operating_limit_offset"]

    periods = [0, 1, 2]

    model = gp.Model("power_generation")
    model.setParam("OutputFlag", 0)

    # Number of generators operating: n[t][p] for type t in period p
    n0 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_gen, name="n0")
    n1 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_gen, name="n1")

    # Power output: x[t][p] total MW from type t in period p
    x0 = model.addVars(periods, vtype=GRB.CONTINUOUS, lb=0.0, name="x0")
    x1 = model.addVars(periods, vtype=GRB.CONTINUOUS, lb=0.0, name="x1")

    # Number of generators started: s[t][p]
    s0 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_gen, name="s0")
    s1 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_gen, name="s1")

    # Objective
    total_cost = gp.quicksum(
        base_cost * (n0[p] + n1[p])
        + power_cost * (x0[p] + x1[p])
        + startup_cost_t0 * s0[p]
        + startup_cost_t1 * s1[p]
        for p in periods
    )
    model.setObjective(total_cost, GRB.MINIMIZE)

    for p in periods:
        # Demand constraint
        model.addConstr(x0[p] + x1[p] >= demand[p], name=f"demand_p{p}")

        # Capacity margin constraint
        model.addConstr(
            max_out_t0 * n0[p] + max_out_t1 * n1[p] >= capacity_margin_demand[p],
            name=f"capacity_margin_p{p}"
        )

        # Power output bounds per type
        model.addConstr(x0[p] >= min_out_t0 * n0[p], name=f"min_out_t0_p{p}")
        model.addConstr(x0[p] <= max_out_t0 * n0[p], name=f"max_out_t0_p{p}")
        model.addConstr(x1[p] >= min_out_t1 * n1[p], name=f"min_out_t1_p{p}")
        model.addConstr(x1[p] <= max_out_t1 * n1[p], name=f"max_out_t1_p{p}")

    # Startup / operating continuity constraints
    # Period 0
    model.addConstr(n0[0] <= offset_t0_p0 + s0[0], name="startup_t0_p0")
    model.addConstr(n1[0] <= offset_t1_p0 + s1[0], name="startup_t1_p0")

    # Periods 1 and 2
    for p in [1, 2]:
        model.addConstr(n0[p] <= n0[p-1] + s0[p], name=f"startup_t0_p{p}")
        model.addConstr(n1[p] <= n1[p-1] + s1[p], name=f"startup_t1_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}