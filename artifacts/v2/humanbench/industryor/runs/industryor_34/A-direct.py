import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    student_counts = params["student_counts"]
    num_schools = params["num_schools"]

    n = len(x_coords)
    villages = range(n)

    model = pyo.ConcreteModel()

    model.build = pyo.Var(villages, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(
            student_counts[i]
            * min(
                ((x_coords[i] - x_coords[j]) ** 2 + (y_coords[i] - y_coords[j]) ** 2) ** 0.5
                for j in villages
                if j != i
            )
            * model.build[i]
            for i in villages
        ),
        sense=pyo.minimize,
    )

    model.num_schools_constraint = pyo.Constraint(
        expr=sum(model.build[i] for i in villages) == num_schools
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}