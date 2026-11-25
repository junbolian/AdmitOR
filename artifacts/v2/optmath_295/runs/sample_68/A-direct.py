import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: one binary per vehicle
    model.x = pyo.Var(range(1, 7), domain=pyo.Binary)

    # Objective: minimize total deployment cost
    model.cost = pyo.Objective(
        expr=(
            params["vehicle_cost_1"] * model.x[1]
            + params["vehicle_cost_2"] * model.x[2]
            + params["vehicle_cost_3"] * model.x[3]
            + params["vehicle_cost_4"] * model.x[4]
            + params["vehicle_cost_5"] * model.x[5]
            + params["vehicle_cost_6"] * model.x[6]
        ),
        sense=pyo.minimize,
    )

    # Route coverage constraints
    # Route 1: Vehicle 6 must be deployed
    model.route_1 = pyo.Constraint(expr=model.x[6] >= 1)

    # Route 2: at least one of Vehicle 2, 4, 6
    model.route_2 = pyo.Constraint(expr=model.x[2] + model.x[4] + model.x[6] >= 1)

    # Route 3: at least one of Vehicle 1, 3, 4
    model.route_3 = pyo.Constraint(expr=model.x[1] + model.x[3] + model.x[4] >= 1)

    # Route 4: Vehicle 3 must be deployed
    model.route_4 = pyo.Constraint(expr=model.x[3] >= 1)

    # Route 5: at least one of Vehicle 1, 5, 6
    model.route_5 = pyo.Constraint(expr=model.x[1] + model.x[5] + model.x[6] >= 1)

    # Route 6: at least one of Vehicle 1, 4
    model.route_6 = pyo.Constraint(expr=model.x[1] + model.x[4] >= 1)

    # Route 7: at least one of Vehicle 3, 5
    model.route_7 = pyo.Constraint(expr=model.x[3] + model.x[5] >= 1)

    # Route 8: Vehicle 4 must be deployed
    model.route_8 = pyo.Constraint(expr=model.x[4] >= 1)

    # Route 9: at least one of Vehicle 3, 5, 6
    model.route_9 = pyo.Constraint(expr=model.x[3] + model.x[5] + model.x[6] >= 1)

    # Route 10: at least one of Vehicle 4, 5, 6
    model.route_10 = pyo.Constraint(expr=model.x[4] + model.x[5] + model.x[6] >= 1)

    # Route 11: at least one of Vehicle 3, 4
    model.route_11 = pyo.Constraint(expr=model.x[3] + model.x[4] >= 1)

    # Route 12: at least one of Vehicle 1, 3, 5, 6
    model.route_12 = pyo.Constraint(
        expr=model.x[1] + model.x[3] + model.x[5] + model.x[6] >= 1
    )

    # Route 13: at least one of Vehicle 3, 4, 6
    model.route_13 = pyo.Constraint(expr=model.x[3] + model.x[4] + model.x[6] >= 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}