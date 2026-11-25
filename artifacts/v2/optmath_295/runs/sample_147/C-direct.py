import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost_type0 = params["base_cost_type0"]
    base_cost_type1 = params["base_cost_type1"]
    var_cost_type0 = params["var_cost_type0"]
    var_cost_type1 = params["var_cost_type1"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    max_units_type0 = params["max_units_type0"]
    max_units_type1 = params["max_units_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    reserve_margin = params["reserve_margin"]
    max_startup_type0_period0 = params["max_startup_type0_period0"]
    max_startup_type1_period0 = params["max_startup_type1_period0"]
    num_periods = params["num_periods"]

    periods = range(num_periods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Number of generators operational per period
    n0 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_units_type0, name="n0")
    n1 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_units_type1, name="n1")

    # Power output per period (continuous)
    p0 = model.addVars(periods, vtype=GRB.CONTINUOUS, lb=0.0, name="p0")
    p1 = model.addVars(periods, vtype=GRB.CONTINUOUS, lb=0.0, name="p1")

    # Startups per period
    s0 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, name="s0")
    s1 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, name="s1")

    # Objective
    model.setObjective(
        gp.quicksum(
            base_cost_type0 * n0[t]
            + base_cost_type1 * n1[t]
            + var_cost_type0 * p0[t]
            + var_cost_type1 * p1[t]
            + startup_cost_type0 * s0[t]
            + startup_cost_type1 * s1[t]
            for t in periods
        ),
        GRB.MINIMIZE
    )

    for t in periods:
        d = demand[t]

        # Demand satisfaction
        model.addConstr(p0[t] + p1[t] >= d, name=f"demand_{t}")

        # Output bounds based on number of units
        model.addConstr(p0[t] >= min_output_type0 * n0[t], name=f"min_p0_{t}")
        model.addConstr(p0[t] <= max_output_type0 * n0[t], name=f"max_p0_{t}")
        model.addConstr(p1[t] >= min_output_type1 * n1[t], name=f"min_p1_{t}")
        model.addConstr(p1[t] <= max_output_type1 * n1[t], name=f"max_p1_{t}")

        # Reserve margin: total max output >= demand * (1 + reserve_margin)
        model.addConstr(
            max_output_type0 * n0[t] + max_output_type1 * n1[t] >= d * (1 + reserve_margin),
            name=f"reserve_{t}"
        )

        # Startup constraints
        if t == 0:
            model.addConstr(s0[t] <= max_startup_type0_period0, name=f"startup0_p0")
            model.addConstr(s1[t] <= max_startup_type1_period0, name=f"startup1_p0")
        else:
            # Startups limited by units operational in previous period
            model.addConstr(s0[t] <= n0[t - 1], name=f"startup0_{t}")
            model.addConstr(s1[t] <= n1[t - 1], name=f"startup1_{t}")

        # Startups cannot exceed units operational this period
        model.addConstr(s0[t] <= n0[t], name=f"startup0_cap_{t}")
        model.addConstr(s1[t] <= n1[t], name=f"startup1_cap_{t}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}