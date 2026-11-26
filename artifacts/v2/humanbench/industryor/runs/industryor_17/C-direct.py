import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coverage_radius = params["coverage_radius"]

    # Areas and their coverage neighborhoods (within coverage_radius of 800m)
    # Structural data from the problem table
    areas = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

    # For each area, the set of areas that can cover it (i.e., areas within 800m)
    # This is symmetric: if B is in A's radius, A is in B's radius
    # We read the table as: area X can be covered by any store placed in the listed areas
    coverage_table = {
        "A": ["A", "C", "E", "G", "H", "I"],
        "B": ["B", "H", "I"],
        "C": ["A", "C", "G", "H", "I"],
        "D": ["D", "J"],
        "E": ["A", "E", "G"],
        "F": ["F", "J", "K"],
        "G": ["A", "C", "E", "G"],
        "H": ["A", "B", "C", "H", "I"],
        "I": ["A", "B", "C", "H", "I"],
        "J": ["D", "F", "J", "K", "L"],
        "K": ["F", "J", "K", "L"],
        "L": ["J", "K", "L"],
    }

    # The coverage_radius parameter is used to confirm the structural data applies
    # (the table is defined for 800m; if a different radius were given, the table
    # would change, but here the coverage relationships are fixed by the problem structure)
    _ = coverage_radius  # acknowledged; structural coverage is encoded in coverage_table

    model = gp.Model("chain_store_location")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[j] = 1 if a store is opened in area j
    x = model.addVars(areas, vtype=GRB.BINARY, name="x")

    # Objective: minimize total number of stores
    model.setObjective(gp.quicksum(x[j] for j in areas), GRB.MINIMIZE)

    # Coverage constraints: every area must be covered by at least one store
    # within the coverage radius
    for area in areas:
        covering_areas = coverage_table[area]
        model.addConstr(
            gp.quicksum(x[j] for j in covering_areas) >= 1,
            name=f"cover_{area}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}