import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    resource_limit = params["resource_limit"]

    profits = [
        381, 336, 352, 361, 344, 358, 371, 342, 367, 349,
        355, 340, 364, 347, 353, 376, 334, 359, 365, 348,
        351, 338, 362, 356, 343, 372, 335, 360, 366, 345,
        354, 341, 363, 350, 357, 374, 333, 368, 369, 346,
        352, 339, 361, 355, 381
    ]
    consumption = [
        0.012048, 0.012821, 0.012500, 0.012346, 0.012658,
        0.012346, 0.012500, 0.012658, 0.012195, 0.012987,
        0.012658, 0.012346, 0.012500, 0.012821, 0.012346,
        0.012500, 0.012658, 0.012195, 0.012500, 0.012346,
        0.012658, 0.012500, 0.012346, 0.012821, 0.012500,
        0.012346, 0.012658, 0.012195, 0.012500, 0.012346,
        0.012658, 0.012500, 0.012346, 0.012821, 0.012500,
        0.012346, 0.012658, 0.012195, 0.012500, 0.012346,
        0.012658, 0.012500, 0.012346, 0.012821, 0.012821
    ]
    upper = [
        716, 606, 635, 691, 612, 628, 663, 597, 681, 619,
        645, 602, 672, 634, 623, 598, 688, 615, 657, 631,
        649, 592, 676, 626, 617, 634, 585, 668, 659, 621,
        642, 606, 671, 604, 653, 589, 682, 664, 613, 637,
        625, 594, 678, 618, 618
    ]

    idx = range(45)

    model = pyo.ConcreteModel()
    model.y = pyo.Var(idx, bounds=lambda _m, i: (0, upper[i]))

    model.profit_expr = pyo.Expression(
        expr=sum(profits[i] * model.y[i] for i in idx)
    )
    model.resource_con = pyo.Constraint(
        expr=sum(consumption[i] * model.y[i] for i in idx) <= resource_limit
    )
    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}