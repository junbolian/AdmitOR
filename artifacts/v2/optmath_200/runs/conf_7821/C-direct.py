import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost_type0 = params["base_cost_type0"]
    base_cost_type1 = params["base_cost_type1"]
    var_cost = params["var_cost"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    demand = params["demand"]  # list of 4 values
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    reserve_margin = params["reserve_margin"]
    max_operating_type0 = params["max_operating_type0"]
    max_operating_type1 = params["max_operating_type1"]
    type1_initial_slack = params["type1_initial_slack"]

    T = 4  # number of periods
    periods = range(T)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # Number of generators operating (integer)
    op0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="op0")
    op1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="op1")

    # Power produced (continuous)
    pw0 = model.addVars(T, vtype=GRB.CONTINUOUS, lb=0, name="pw0")
    pw1 = model.addVars(T, vtype=GRB.CONTINUOUS, lb=0, name="pw1")

    # Number of generators started (integer)
    st0 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="st0")
    st1 = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="st1")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            base_cost_type0 * op0[t] + base_cost_type1 * op1[t]
            + var_cost * pw0[t] + var_cost * pw1[t]
            + startup_cost_type0 * st0[t] + startup_cost_type1 * st1[t]
            for t in periods
        ),
        GRB.MINIMIZE
    )

    for t in periods:
        # Demand constraint
        model.addConstr(pw0[t] + pw1[t] >= demand[t], name=f"demand_{t}")

        # Reserve margin constraint
        model.addConstr(
            max_output_type0 * op0[t] + max_output_type1 * op1[t] >= demand[t] * (1 + reserve_margin),
            name=f"reserve_{t}"
        )

        # Max operating constraints
        model.addConstr(op0[t] <= max_operating_type0, name=f"max_op0_{t}")
        model.addConstr(op1[t] <= max_operating_type1, name=f"max_op1_{t}")

        # Output bounds based on number operating
        model.addConstr(pw0[t] >= min_output_type0 * op0[t], name=f"min_pw0_{t}")
        model.addConstr(pw0[t] <= max_output_type0 * op0[t], name=f"max_pw0_{t}")
        model.addConstr(pw1[t] >= min_output_type1 * op1[t], name=f"min_pw1_{t}")
        model.addConstr(pw1[t] <= max_output_type1 * op1[t], name=f"max_pw1_{t}")

    # Startup / operating constraints for Type 0
    # Period 0: op0[0] <= 0 (initial available, assumed 0 since not provided) + st0[0]
    # The problem says "number of generators available at the start plus started in period 0"
    # Since no initial count is given, we interpret available_at_start = 0
    model.addConstr(op0[0] <= st0[0], name="startup_op0_0")

    for t in range(1, T):
        model.addConstr(op0[t] <= op0[t-1] + st0[t], name=f"startup_op0_{t}")

    # Startup / operating constraints for Type 1
    # Period 0: op1[0] - st1[0] <= type1_initial_slack
    model.addConstr(op1[0] - st1[0] <= type1_initial_slack, name="startup_op1_0")

    for t in range(1, T):
        model.addConstr(op1[t] - st1[t] <= op1[t-1], name=f"startup_op1_{t}")

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