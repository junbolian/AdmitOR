import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    facility_cost = params["facility_cost"]
    num_facilities = params["num_facilities"]
    num_service_areas = params["num_service_areas"]
    coverage_requirement = params["coverage_requirement"]

    coverage_lists = {
        1: [1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 18, 21],
        2: [1, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 19, 20],
        3: [4, 5, 6, 7, 8, 10, 18, 20, 21],
        4: [4, 5, 6, 9, 10, 11, 13, 14, 16, 17, 18, 19, 20, 21],
        5: [1, 2, 4, 9, 10, 11, 12, 13, 14, 15, 20],
        6: [1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 14, 15, 16, 18, 19, 21],
        7: [4, 5, 9, 10, 12, 14, 16, 17, 18, 20, 21],
        8: [2, 3, 4, 5, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20],
        9: [1, 2, 6, 11, 13, 14, 18, 20, 21],
        10: [1, 3, 5, 8, 11, 13, 14, 16, 17, 21],
        11: [1, 2, 3, 7, 8, 9, 10, 12, 15, 16, 17, 18, 19],
        12: [1, 2, 3, 4, 5, 13, 14, 15, 16, 17, 19, 21],
        13: [4, 5, 6, 7, 8, 12, 14, 15, 17, 18, 19, 21],
        14: [1, 2, 4, 5, 7, 9, 10, 11, 16, 17, 20, 21],
        15: [1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 16, 17, 21],
        16: [3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21],
        17: [4, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21],
        18: [3, 4, 5, 7, 8, 9, 13, 15, 18, 19, 20],
        19: [2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        20: [3, 6, 7, 8, 9, 10, 11, 12, 15, 16, 19, 21],
        21: [1, 2, 3, 4, 6, 7, 9, 11, 14, 17, 19],
        22: [1, 2, 4, 5, 6, 8, 10, 11, 14, 17, 18, 19, 20],
        23: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 21],
        24: [1, 2, 3, 4, 5, 8, 10, 11, 13, 14, 15, 16, 18, 20, 21],
        25: [2, 3, 8, 9, 10, 11, 13, 14, 15, 17, 18, 20],
        26: [1, 2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 18, 20, 21],
        27: [7, 8, 10, 12, 13, 14, 15, 16, 17, 18, 20],
        28: [4, 7, 8, 10, 11, 13, 14, 16, 17, 20, 21],
        29: [1, 4, 5, 6, 7, 10, 11, 12, 13, 15, 16, 18, 19, 21],
        30: [3, 6, 9, 11, 12, 15, 16, 21],
        31: [1, 3, 4, 10, 13, 14, 15, 18, 19, 21],
        32: [1, 2, 4, 10, 11, 13, 15, 16, 18, 20],
        33: [2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 17, 18, 19, 20, 21],
        34: [1, 4, 11, 12, 13, 14, 15, 16, 18, 20, 21],
        35: [2, 3, 5, 7, 9, 11, 13, 15, 16, 17, 18, 19, 20],
        36: [1, 3, 4, 5, 6, 7, 8, 9, 11, 13, 15, 16, 17, 19, 20, 21],
    }

    model = pyo.ConcreteModel()
    model.FAC = pyo.RangeSet(1, num_facilities)
    model.SA = pyo.RangeSet(1, num_service_areas)

    model.x = pyo.Var(model.FAC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(facility_cost[i - 1] * m.x[i] for i in m.FAC)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, j):
        return sum(m.x[i] for i in coverage_lists[j]) >= coverage_requirement

    model.cover = pyo.Constraint(model.SA, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}