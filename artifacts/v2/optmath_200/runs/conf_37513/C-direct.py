import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_p0_0_1 = params["cost_p0_0_1"]
    cost_p0_1_0 = params["cost_p0_1_0"]
    cost_p1_0_1 = params["cost_p1_0_1"]
    cost_p1_1_0 = params["cost_p1_1_0"]
    capacity_p0 = params["capacity_p0"]
    capacity_p1 = params["capacity_p1"]
    demand_1_0 = params["demand_1_0"]
    avail_p0 = params["avail_p0"]
    avail_p1 = params["avail_p1"]
    max_deploy_1_0 = params["max_deploy_1_0"]

    model = gp.Model("plane_deployment")
    model.setParam("OutputFlag", 0)

    # Decision variables: planes deployed from i to j for each plane type
    # deploy_p0_0_1: Plane 0 deployed from Location 0 to Location 1
    # deploy_p0_1_0: Plane 0 deployed from Location 1 to Location 0
    # deploy_p1_0_1: Plane 1 deployed from Location 0 to Location 1
    # deploy_p1_1_0: Plane 1 deployed from Location 1 to Location 0
    deploy_p0_0_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="deploy_p0_0_1")
    deploy_p0_1_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="deploy_p0_1_0")
    deploy_p1_0_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="deploy_p1_0_1")
    deploy_p1_1_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="deploy_p1_1_0")

    # Idle planes at start of period at each location for each plane type
    idle_p0_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p0_0")
    idle_p0_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p0_1")
    idle_p1_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p1_0")
    idle_p1_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p1_1")

    # Initial idle planes at each location (before deployment)
    # The initial number of idle planes = idle at start + planes deployed from that location
    # So: initial_idle_p0_loc0 = idle_p0_0 + deploy_p0_0_1
    # These initial values must be consistent - we treat them as derived quantities.
    # The constraint is: initial_idle = idle_start + deployed_out
    # We need: total initial idle <= avail for each type

    # Availability constraints: total initial idle planes across locations <= avail
    # initial_p0_loc0 = idle_p0_0 + deploy_p0_0_1
    # initial_p0_loc1 = idle_p0_1 + deploy_p0_1_0
    # sum of initials <= avail_p0
    model.addConstr(
        (idle_p0_0 + deploy_p0_0_1) + (idle_p0_1 + deploy_p0_1_0) <= avail_p0,
        name="avail_constr_p0"
    )
    model.addConstr(
        (idle_p1_0 + deploy_p1_0_1) + (idle_p1_1 + deploy_p1_1_0) <= avail_p1,
        name="avail_constr_p1"
    )

    # Demand constraint: capacity on route 1->0 must meet demand
    model.addConstr(
        capacity_p0 * deploy_p0_1_0 + capacity_p1 * deploy_p1_1_0 >= demand_1_0,
        name="demand_1_0"
    )

    # Route restrictions: no planes deployed from Location 0 to Location 1
    model.addConstr(deploy_p0_0_1 == 0, name="no_deploy_p0_0_1")
    model.addConstr(deploy_p1_0_1 == 0, name="no_deploy_p1_0_1")

    # Maximum planes deployed from Location 1 to Location 0
    model.addConstr(deploy_p0_1_0 <= max_deploy_1_0, name="max_deploy_p0_1_0")
    model.addConstr(deploy_p1_1_0 <= max_deploy_1_0, name="max_deploy_p1_1_0")

    # Objective: minimize total deployment cost
    model.setObjective(
        cost_p0_0_1 * deploy_p0_0_1 +
        cost_p0_1_0 * deploy_p0_1_0 +
        cost_p1_0_1 * deploy_p1_0_1 +
        cost_p1_1_0 * deploy_p1_1_0,
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