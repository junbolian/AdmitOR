import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    products = ["truck", "airplane", "boat", "train"]

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    profits = {
        "truck": params["profit_truck"],
        "airplane": params["profit_airplane"],
        "boat": params["profit_boat"],
        "train": params["profit_train"],
    }

    wood_req = {
        "truck": params["wood_truck"],
        "airplane": params["wood_airplane"],
        "boat": params["wood_boat"],
        "train": params["wood_train"],
    }

    steel_req = {
        "truck": params["steel_truck"],
        "airplane": params["steel_airplane"],
        "boat": params["steel_boat"],
        "train": params["steel_train"],
    }

    model.obj = pyo.Objective(
        expr=sum(profits[p] * model.x[p] for p in products),
        sense=pyo.maximize,
    )

    model.wood_con = pyo.Constraint(
        expr=sum(wood_req[p] * model.x[p] for p in products)
        <= params["wood_capacity"]
    )

    model.steel_con = pyo.Constraint(
        expr=sum(steel_req[p] * model.x[p] for p in products)
        <= params["steel_capacity"]
    )

    # If trucks are manufactured, trains must not be manufactured.
    # Big-M style with indicator via linear constraint using a binary.
    big_m = params["wood_capacity"] + params["steel_capacity"]

    model.y_truck = pyo.Var(domain=pyo.Binary)
    model.y_train = pyo.Var(domain=pyo.Binary)

    model.truck_link = pyo.Constraint(expr=model.x["truck"] <= big_m * model.y_truck)
    model.train_link = pyo.Constraint(expr=model.x["train"] <= big_m * model.y_train)
    model.truck_train_excl = pyo.Constraint(expr=model.y_truck + model.y_train <= 1)

    # If boats are manufactured, airplanes must also be manufactured.
    model.y_boat = pyo.Var(domain=pyo.Binary)
    model.y_airplane = pyo.Var(domain=pyo.Binary)

    model.boat_link = pyo.Constraint(expr=model.x["boat"] <= big_m * model.y_boat)
    model.airplane_link = pyo.Constraint(expr=model.x["airplane"] <= big_m * model.y_airplane)
    model.boat_implies_airplane = pyo.Constraint(expr=model.y_boat <= model.y_airplane)

    # Boats cannot exceed trains.
    model.boat_train_con = pyo.Constraint(expr=model.x["boat"] <= model.x["train"])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}