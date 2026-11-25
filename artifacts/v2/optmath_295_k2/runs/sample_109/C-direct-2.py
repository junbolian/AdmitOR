import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost = params["base_cost"]
    marginal_cost = params["marginal_cost"]
    startup_cost = params["startup_cost"]
    demand = params["demand"]
    min_output = params["min_output"]
    max_output = params["max_output"]
    max_generators = params["max_generators"]
    reserve_requirement = params["reserve_requirement"]
    initial_startup_bound = params["initial_startup_bound"]

    num_types = 3
    num_periods = 5
    types = range(num_types)
    periods = range(num_periods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # generators[g, t]: number of active generators of type g in period t
    generators = model.addVars(num_types, num_periods, vtype=GRB.INTEGER, lb=0, name="generators")
    # power[g, t]: total MW output from type g in period t
    power = model.addVars(num_types, num_periods, vtype=GRB.CONTINUOUS, lb=0.0, name="power")
    # startups[g, t]: number of startups of type g in period t
    startups = model.addVars(num_types, num_periods, vtype=GRB.INTEGER, lb=0, name="startups")

    # Objective: minimize total cost
    obj = gp.quicksum(
        base_cost[g] * generators[g, t]
        + marginal_cost[g] * power[g, t]
        + startup_cost[g] * startups[g, t]
        for g in types for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraint: meet demand in each period
    for t in periods:
        model.addConstr(
            gp.quicksum(power[g, t] for g in types) >= demand[t],
            name=f"demand_{t}"
        )

    # Constraint: generator capacity limits
    for g in types:
        for t in periods:
            # Total output >= min_output * active generators
            model.addConstr(
                power[g, t] >= min_output[g] * generators[g, t],
                name=f"min_output_{g}_{t}"
            )
            # Total output <= max_output * active generators
            model.addConstr(
                power[g, t] <= max_output[g] * generators[g, t],
                name=f"max_output_{g}_{t}"
            )

    # Constraint: generator availability
    for g in types:
        for t in periods:
            model.addConstr(
                generators[g, t] <= max_generators[g],
                name=f"max_gen_{g}_{t}"
            )

    # Constraint: reserve capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(max_output[g] * generators[g, t] for g in types) >= reserve_requirement[t],
            name=f"reserve_{t}"
        )

    # Constraint: startup logic
    for g in types:
        # Period 0: generators[g, 0] <= startups[g, 0] + initial_startup_bound[g]
        model.addConstr(
            generators[g, 0] <= startups[g, 0] + initial_startup_bound[g],
            name=f"startup_init_{g}"
        )
        # Subsequent periods: generators[g, t] <= generators[g, t-1] + startups[g, t]
        for t in range(1, num_periods):
            model.addConstr(
                generators[g, t] <= generators[g, t - 1] + startups[g, t],
                name=f"startup_{g}_{t}"
            )

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