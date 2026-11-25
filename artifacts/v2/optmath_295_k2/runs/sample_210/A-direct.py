import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Number of locations and zones
    num_locations = 13
    num_zones = 21

    # Setup costs
    setup_costs = [params[f"setup_cost_{i}"] for i in range(1, num_locations + 1)]

    # Coverage relationships: zone -> list of locations that can cover it
    coverage = {
        1: [1, 2, 4, 6, 7, 8, 11],
        2: [3, 4, 5, 6, 7, 9, 11, 13],
        3: [1, 3, 4, 5, 7, 8, 9, 10, 11],
        4: [1, 4, 8, 10, 13],
        5: [1, 2, 4, 6, 9, 10],
        6: [3, 4, 5, 6, 7, 8, 10, 13],
        7: [2, 4, 5, 6, 7, 9, 10, 11, 12, 13],
        8: [5, 8, 11, 12],
        9: [1, 3, 4, 7, 8, 10, 12, 13],
        10: [2, 4, 6, 8, 11, 12],
        11: [3, 4, 8, 9, 11],
        12: [2, 4, 5, 7, 11, 12],
        13: [1, 2, 3, 5, 7, 9, 10, 13],
        14: [1, 2, 6, 8, 9, 10, 12, 13],
        15: [1, 3, 5, 10],
        16: [1, 5, 6, 8, 13],
        17: [1, 2, 3, 4, 5, 6, 8, 9, 12],
        18: [1, 4, 6, 9, 11, 13],
        19: [4, 6, 8],
        20: [1, 2, 3, 4, 5, 11, 13],
        21: [2, 3, 6, 9],
    }

    # Build model
    model = pyo.ConcreteModel()

    # Decision variables: x[i] = 1 if location i is selected, 0 otherwise
    model.x = pyo.Var(range(1, num_locations + 1), domain=pyo.Binary)

    # Objective: minimize total setup cost
    model.obj = pyo.Objective(
        expr=sum(setup_costs[i - 1] * model.x[i] for i in range(1, num_locations + 1)),
        sense=pyo.minimize,
    )

    # Constraints: each zone must be covered by at least one selected location
    model.cover_constr = pyo.ConstraintList()
    for zone in range(1, num_zones + 1):
        model.cover_constr.add(
            sum(model.x[loc] for loc in coverage[zone]) >= 1
        )

    # Solve with HiGHS
    solver = Highs()
    solver.solve(model)

    # Retrieve objective value
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "infeasible"}