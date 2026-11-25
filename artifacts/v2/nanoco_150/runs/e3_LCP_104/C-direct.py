import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_tasks = params["num_tasks"]
    num_nodes = params["num_nodes"]
    num_conflict_pairs = params["num_conflict_pairs"]
    conflict_pairs = params["conflict_pairs"]
    allowable_nodes = params["allowable_nodes"]

    tasks = range(num_tasks)
    nodes = range(num_nodes)

    model = gp.Model("task_assignment")

    # x[t, n] = 1 if task t is assigned to node n
    x = {}
    for t in tasks:
        for n in allowable_nodes[t]:
            x[t, n] = model.addVar(vtype=GRB.BINARY, name=f"x_{t}_{n}")

    # z = maximum node ID utilized
    z = model.addVar(vtype=GRB.INTEGER, name="z", lb=0, ub=num_nodes - 1)

    model.setObjective(z, GRB.MINIMIZE)

    # Each task assigned to exactly one allowable node
    for t in tasks:
        model.addConstr(
            gp.quicksum(x[t, n] for n in allowable_nodes[t]) == 1,
            name=f"assign_{t}",
        )

    # Conflict pairs: the two tasks must be on distinct nodes
    for idx, (i, j) in enumerate(conflict_pairs):
        common_nodes = set(allowable_nodes[i]) & set(allowable_nodes[j])
        for n in common_nodes:
            model.addConstr(
                x[i, n] + x[j, n] <= 1,
                name=f"conflict_{idx}_{i}_{j}_node{n}",
            )

    # z >= n for every node n that is used by some task
    for t in tasks:
        for n in allowable_nodes[t]:
            model.addConstr(z >= n * x[t, n], name=f"link_z_{t}_{n}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        reason = (
            "infeasible"
            if model.status == GRB.INFEASIBLE
            else f"status_{model.status}"
        )
        return {"objective": None, "status": reason}