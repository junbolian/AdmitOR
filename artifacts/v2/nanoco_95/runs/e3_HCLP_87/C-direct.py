import gurobipy as gp
from gurobipy import GRB

def solve(params):
    construction_costs = params["construction_costs"]
    node_demands = params["node_demands"]
    bonus_values = params["bonus_values"]
    R1 = params["R1_safe_range"]
    R2 = params["R2_ultra_range"]
    distance_matrix = params["distance_matrix"]

    num_nodes = 20
    num_sites = 14
    nodes = range(num_nodes)
    sites = range(num_sites)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = 1 if site j is activated
    x = model.addVars(sites, vtype=GRB.BINARY, name="x")
    # u[i] = 1 if node i gets ultra-fast credit (within R2 of at least one activated site)
    u = model.addVars(nodes, vtype=GRB.BINARY, name="u")

    # Hard coverage: every node i must be within R1 of at least one activated site
    for i in nodes:
        eligible = [j for j in sites if distance_matrix[i][j] <= R1]
        if not eligible:
            return {"objective": None, "status": "infeasible: node has no site within R1"}
        model.addConstr(gp.quicksum(x[j] for j in eligible) >= 1, name=f"cover_{i}")

    # Ultra-fast credit: u[i] can be 1 only if at least one activated site is within R2 of node i
    for i in nodes:
        ultra_sites = [j for j in sites if distance_matrix[i][j] <= R2]
        if not ultra_sites:
            # No site can serve node i within R2; force u[i] = 0
            model.addConstr(u[i] == 0, name=f"no_ultra_{i}")
        else:
            # u[i] <= sum of x[j] for ultra-eligible sites (u[i]=1 requires at least one open)
            model.addConstr(u[i] <= gp.quicksum(x[j] for j in ultra_sites), name=f"ultra_{i}")

    # Objective: minimize total construction cost minus total ultra-fast incentive credits
    total_construction = gp.quicksum(construction_costs[j] * x[j] for j in sites)
    total_bonus = gp.quicksum(bonus_values[i] * u[i] for i in nodes)
    model.setObjective(total_construction - total_bonus, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}