import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    max_turbines_per_feeder = params["max_turbines_per_feeder"]
    num_nodes = params["num_nodes"]
    num_turbines = params["num_turbines"]

    nodes = list(range(num_nodes))
    turbines = list(range(1, num_nodes))

    model = gp.Model("radial_collector")
    model.Params.OutputFlag = 0

    # Directed arcs away from root: (i, j) where j is a turbine and i != j
    arcs = [(i, j) for i in nodes for j in turbines if i != j]

    # y[i,j] = 1 if arc i->j is selected (i is parent of j)
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # f[i,j] = flow (number of turbines downstream of arc i->j)
    f = model.addVars(arcs, vtype=GRB.CONTINUOUS, lb=0, name="f")

    # Minimize total cable installation cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * y[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each turbine has exactly one incoming arc (one parent)
    for j in turbines:
        model.addConstr(
            gp.quicksum(y[i, j] for i in nodes if i != j) == 1,
            name=f"in_deg_{j}"
        )

    # Total flow leaving the root equals total turbines
    model.addConstr(
        gp.quicksum(f[0, j] for j in turbines) == num_turbines,
        name="root_outflow"
    )

    # Flow conservation: inflow = 1 (consumed) + outflow
    for j in turbines:
        model.addConstr(
            gp.quicksum(f[i, j] for i in nodes if i != j)
            == 1 + gp.quicksum(f[j, k] for k in turbines if k != j),
            name=f"flow_con_{j}"
        )

    # Flow can only exist on selected arcs
    for (i, j) in arcs:
        model.addConstr(f[i, j] <= num_turbines * y[i, j], name=f"link_{i}_{j}")

    # Feeder string capacity: subtree rooted at each direct child of root
    # has at most max_turbines_per_feeder turbines
    for j in turbines:
        model.addConstr(
            f[0, j] <= max_turbines_per_feeder * y[0, j],
            name=f"cap_{j}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}