import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    max_turbines_per_feeder = params["max_turbines_per_feeder"]
    num_nodes = params["num_nodes"]
    num_turbines = params["num_turbines"]

    nodes = list(range(num_nodes))
    turbines = list(range(1, num_nodes))

    edges = [(i, j) for i in range(num_nodes) for j in range(i + 1, num_nodes)]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("offshore_wind_collector")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 300)

    # x[i,j] = 1 if undirected edge (i<j) is in the tree
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # f[i,j] = commodity flow on directed arc (i,j)
    # Each turbine k sends 1 unit toward root 0; root is sink absorbing num_turbines units.
    # This is the standard single-commodity flow subtour elimination for spanning trees.
    f = model.addVars(arcs, lb=0.0, ub=float(num_turbines), vtype=GRB.CONTINUOUS, name="f")

    # Objective: minimize total cable cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for (i, j) in edges),
        GRB.MINIMIZE
    )

    # Exactly num_nodes - 1 edges (spanning tree)
    model.addConstr(
        gp.quicksum(x[i, j] for (i, j) in edges) == num_nodes - 1,
        name="tree_size"
    )

    # Flow conservation: root 0 is sink, absorbs num_turbines units
    model.addConstr(
        gp.quicksum(f[k, 0] for k in turbines) -
        gp.quicksum(f[0, k] for k in turbines) == num_turbines,
        name="flow_root"
    )

    # Each turbine is a source of 1 unit flowing toward root
    for k in turbines:
        neighbors = [v for v in nodes if v != k]
        model.addConstr(
            gp.quicksum(f[k, v] for v in neighbors) -
            gp.quicksum(f[v, k] for v in neighbors) == 1,
            name=f"flow_turbine_{k}"
        )

    # Flow only allowed on selected edges (in either direction)
    for (i, j) in edges:
        model.addConstr(f[i, j] <= num_turbines * x[i, j], name=f"fcap_fwd_{i}_{j}")
        model.addConstr(f[j, i] <= num_turbines * x[i, j], name=f"fcap_bwd_{i}_{j}")

    # Feeder capacity: in tree rooted at 0 with flow going toward root,
    # flow on arc (j, 0) = number of turbines in the subtree rooted at j
    # (the feeder connected to 0 via edge (0,j)).
    # We limit this to max_turbines_per_feeder.
    for j in turbines:
        model.addConstr(f[j, 0] <= max_turbines_per_feeder, name=f"feeder_cap_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.TIME_LIMIT and model.SolCount > 0:
        return {"objective": float(model.ObjVal), "status": "time_limit_feasible"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}