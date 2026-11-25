import gurobipy as gp
from gurobipy import GRB

LINK_EDGES = [
    (0, 1), (0, 2), (0, 3), (0, 5), (0, 7),
    (1, 5), (1, 7), (2, 3), (2, 6), (2, 7),
    (2, 8), (3, 7), (4, 5), (4, 6), (5, 7), (5, 8),
]
NUM_CELLS = 9
NUM_LINKS = len(LINK_EDGES)


def solve(params):
    link_weights = params["link_weights"]
    cell_capacities = params["cell_capacities"]

    if len(link_weights) != NUM_LINKS:
        raise ValueError(
            f"link_weights must have {NUM_LINKS} entries, got {len(link_weights)}"
        )
    if len(cell_capacities) != NUM_CELLS:
        raise ValueError(
            f"cell_capacities must have {NUM_CELLS} entries, got {len(cell_capacities)}"
        )

    model = gp.Model("manufacturing_task_assignment")
    model.Params.OutputFlag = 0

    x = model.addVars(NUM_LINKS, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(link_weights[k] * x[k] for k in range(NUM_LINKS)),
        sense=GRB.MAXIMIZE,
    )

    for c in range(NUM_CELLS):
        incident = [
            k for k, (i, j) in enumerate(LINK_EDGES) if i == c or j == c
        ]
        if incident:
            model.addConstr(
                gp.quicksum(x[k] for k in incident) <= cell_capacities[c],
                name=f"capacity_cell_{c}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}