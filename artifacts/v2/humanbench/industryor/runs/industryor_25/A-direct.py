import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    mines = ["A", "B"]
    areas = ["1", "2", "3"]

    model.x = pyo.Var(mines, areas, domain=pyo.NonNegativeReals)

    dist = {
        ("A", "1"): params["dist_A1"],
        ("A", "2"): params["dist_A2"],
        ("A", "3"): params["dist_A3"],
        ("B", "1"): params["dist_B1"],
        ("B", "2"): params["dist_B2"],
        ("B", "3"): params["dist_B3"],
    }

    demand = {
        "1": params["demand_1"],
        "2": params["demand_2"],
        "3": params["demand_3"],
    }

    supply_lower = {
        "A": params["supply_A_lower"],
        "B": params["supply_B_lower"],
    }

    model.obj = pyo.Objective(
        expr=sum(dist[(i, j)] * model.x[i, j] for i in mines for j in areas),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        areas,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mines) == demand[j],
    )

    model.supply_con = pyo.Constraint(
        mines,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in areas) >= supply_lower[i],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}