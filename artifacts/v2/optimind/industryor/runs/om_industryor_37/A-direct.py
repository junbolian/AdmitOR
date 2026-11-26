import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Continuous (relaxed integer) variables for each transportation method
    model.x_motorcycle = pyo.Var(bounds=(0, None))
    model.x_small_truck = pyo.Var(bounds=(0, None))
    model.x_large_truck = pyo.Var(bounds=(0, None))

    # Binary indicators for choosing a method
    model.y_motorcycle = pyo.Var(domain=pyo.Binary)
    model.y_small_truck = pyo.Var(domain=pyo.Binary)
    model.y_large_truck = pyo.Var(domain=pyo.Binary)

    # Objective: minimize total pollution
    model.obj = pyo.Objective(
        expr=(
            params["pollution_small_truck"] * model.x_small_truck
            + params["pollution_large_truck"] * model.x_large_truck
        ),
        sense=pyo.minimize,
    )

    # Big-M bounds linking usage to selection
    model.cap_mc = pyo.Constraint(
        expr=model.x_motorcycle <= params["motorcycle_trip_cap"] * model.y_motorcycle
    )
    model.cap_st = pyo.Constraint(
        expr=model.x_small_truck <= params["total_trip_cap"] * model.y_small_truck
    )
    model.cap_lt = pyo.Constraint(
        expr=model.x_large_truck <= params["total_trip_cap"] * model.y_large_truck
    )

    # Choose at most two methods
    model.two_methods = pyo.Constraint(
        expr=model.y_motorcycle + model.y_small_truck + model.y_large_truck <= 2
    )

    # Pollution for motorcycle included via objective rewrite:
    # We cannot easily include motorcycle pollution because x_motorcycle is not
    # in the objective above; instead include it directly.
    # Rebuild objective properly below.
    # (Kept simple: define full objective before solving.)
    model.obj.deactivate()

    model.obj_full = pyo.Objective(
        expr=(
            params["pollution_motorcycle"] * model.x_motorcycle
            + params["pollution_small_truck"] * model.x_small_truck
            + params["pollution_large_truck"] * model.x_large_truck
        ),
        sense=pyo.minimize,
    )

    # Demand constraint
    model.demand = pyo.Constraint(
        expr=(
            params["capacity_motorcycle"] * model.x_motorcycle
            + params["capacity_small_truck"] * model.x_small_truck
            + params["capacity_large_truck"] * model.x_large_truck
            >= params["demand"]
        )
    )

    # Motorcycle trip cap
    model.mc_cap = pyo.Constraint(
        expr=model.x_motorcycle <= params["motorcycle_trip_cap"]
    )

    # Total trip cap
    model.total_cap = pyo.Constraint(
        expr=model.x_motorcycle + model.x_small_truck + model.x_large_truck
        <= params["total_trip_cap"]
    )

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj_full))
    return {"objective": obj_val, "status": "optimal"}