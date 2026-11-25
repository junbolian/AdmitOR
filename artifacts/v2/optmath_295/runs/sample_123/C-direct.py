import gurobipy as gp
from gurobipy import GRB

def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]

    # Coverage sets: which towers can cover each region
    region_towers = {
        0: [0, 3, 5, 6],
        1: [2, 3, 4, 6],
        2: [0, 1, 4, 5, 6],
        3: [0, 3, 4],
        4: [0, 3, 4],
        5: [1, 2, 3],
        6: [1, 2, 3, 4],
        7: [1, 2, 3, 4, 5, 6],
        8: [0, 1, 2, 4, 5],
        9: [1, 4, 6],
    }

    num_regions = len(populations)
    num_towers = len(tower_costs)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variables: build tower j, cover region i
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    cover = model.addVars(num_regions, vtype=GRB.BINARY, name="cover")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(populations[i] * cover[i] for i in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_costs[j] * build[j] for j in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: region i covered only if at least one relevant tower is built
    for i in range(num_regions):
        towers = region_towers[i]
        # cover[i] <= sum of build[j] for j in towers
        model.addConstr(
            cover[i] <= gp.quicksum(build[j] for j in towers),
            name=f"coverage_{i}"
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