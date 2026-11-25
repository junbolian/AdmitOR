import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_p0_0to1 = params["cost_p0_0to1"]
    cost_p0_1to0 = params["cost_p0_1to0"]
    cost_p1_0to1 = params["cost_p1_0to1"]
    cost_p1_1to0 = params["cost_p1_1to0"]
    max_planes_p0 = params["max_planes_p0"]
    max_planes_p1 = params["max_planes_p1"]
    demand_0to1 = params["demand_0to1"]
    capacity_p0 = params["capacity_p0"]
    capacity_p1 = params["capacity_p1"]
    max_ops_p0_0to1 = params["max_ops_p0_0to1"]
    max_ops_p1_0to1 = params["max_ops_p1_0to1"]
    max_ops_p0_1to0 = params["max_ops_p0_1to0"]
    max_ops_p1_1to0 = params["max_ops_p1_1to0"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: number of planes operated on each route
    x_p0_0to1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_p0_0to1")
    x_p0_1to0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_p0_1to0")
    x_p1_0to1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_p1_0to1")
    x_p1_1to0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_p1_1to0")

    # Idle planes at each location for each plane type
    idle_p0_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p0_loc0")
    idle_p0_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p0_loc1")
    idle_p1_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p1_loc0")
    idle_p1_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p1_loc1")

    # Objective: minimize total operational cost
    model.setObjective(
        cost_p0_0to1 * x_p0_0to1 +
        cost_p0_1to0 * x_p0_1to0 +
        cost_p1_0to1 * x_p1_0to1 +
        cost_p1_1to0 * x_p1_1to0,
        GRB.MINIMIZE
    )

    # Fleet availability: total planes of each type (operating + idle) <= max available
    model.addConstr(x_p0_0to1 + x_p0_1to0 + idle_p0_loc0 + idle_p0_loc1 == max_planes_p0,
                    name="fleet_p0")
    model.addConstr(x_p1_0to1 + x_p1_1to0 + idle_p1_loc0 + idle_p1_loc1 == max_planes_p1,
                    name="fleet_p1")

    # Demand constraint: total capacity on route 0->1 must meet demand
    model.addConstr(
        capacity_p0 * x_p0_0to1 + capacity_p1 * x_p1_0to1 >= demand_0to1,
        name="demand_0to1"
    )

    # Route operation limits
    model.addConstr(x_p0_0to1 <= max_ops_p0_0to1, name="max_ops_p0_0to1")
    model.addConstr(x_p1_0to1 <= max_ops_p1_0to1, name="max_ops_p1_0to1")
    model.addConstr(x_p0_1to0 <= max_ops_p0_1to0, name="max_ops_p0_1to0")
    model.addConstr(x_p1_1to0 <= max_ops_p1_1to0, name="max_ops_p1_1to0")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}