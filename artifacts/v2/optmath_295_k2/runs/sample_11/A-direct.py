import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    resource_limit = params["resource_limit"]

    profits = [
        381, 336, 352, 319, 412, 371, 424, 362, 393, 415,
        351, 378, 419, 344, 420, 391, 432, 437, 364, 388,
        349, 389, 345, 430, 440, 345, 339, 439, 355, 372,
        431, 387, 378, 411, 315, 341, 345, 392, 318, 433,
        332, 440, 385, 383, 381
    ]

    consumption = [
        0.012048, 0.012821, 0.011876, 0.013158, 0.010989, 0.012048, 0.010989, 0.012346, 0.012987, 0.011765,
        0.013158, 0.012048, 0.011111, 0.012987, 0.010989, 0.012500, 0.010989, 0.011236, 0.012500, 0.012048,
        0.013158, 0.012346, 0.012500, 0.010989, 0.010989, 0.012987, 0.012346, 0.010989, 0.012987, 0.012500,
        0.011111, 0.012500, 0.011765, 0.010989, 0.013158, 0.012987, 0.012346, 0.011765, 0.013158, 0.011765,
        0.012987, 0.010989, 0.012048, 0.011765, 0.012821
    ]

    upper_limits = [
        716, 606, 635, 584, 754, 687, 779, 671, 692, 748,
        645, 673, 764, 614, 758, 706, 763, 800, 654, 690,
        631, 700, 648, 742, 791, 617, 612, 754, 637, 668,
        765, 697, 681, 733, 558, 602, 612, 706, 564, 776,
        593, 772, 686, 684, 618
    ]

    n = 45
    model = pyo.ConcreteModel()

    model.idx = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.idx, domain=pyo.NonNegativeReals)

    def profit_rule(m, i):
        return profits[i] * m.x[i]
    model.profit_expr = pyo.Expression(model.idx, rule=profit_rule)

    def resource_rule(m):
        return sum(consumption[i] * m.x[i] for i in m.idx) <= resource_limit
    model.resource_con = pyo.Constraint(rule=resource_rule)

    def ub_rule(m, i):
        return m.x[i] <= upper_limits[i]
    model.ub_con = pyo.Constraint(model.idx, rule=ub_rule)

    def obj_rule(m):
        return sum(m.profit_expr[i] for i in m.idx)
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}