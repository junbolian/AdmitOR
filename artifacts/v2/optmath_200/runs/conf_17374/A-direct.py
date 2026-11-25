import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    teams = list(range(1, 15))

    team_cost = {
        1: params["team_cost_1"],
        2: params["team_cost_2"],
        3: params["team_cost_3"],
        4: params["team_cost_4"],
        5: params["team_cost_5"],
        6: params["team_cost_6"],
        7: params["team_cost_7"],
        8: params["team_cost_8"],
        9: params["team_cost_9"],
        10: params["team_cost_10"],
        11: params["team_cost_11"],
        12: params["team_cost_12"],
        13: params["team_cost_13"],
        14: params["team_cost_14"],
    }

    coverage_sets = {
        1: ([4, 5, 9, 12, 13, 14], params["coverage_req_1"]),
        2: ([4, 5, 8], params["coverage_req_2"]),
        3: ([1, 4, 8, 10, 12], params["coverage_req_3"]),
        4: ([3, 7, 8, 11, 12, 14], params["coverage_req_4"]),
        5: ([4, 5, 9, 14], params["coverage_req_5"]),
        6: ([4, 5, 9, 10, 11, 12, 13], params["coverage_req_6"]),
        7: ([2, 4, 6, 7, 11], params["coverage_req_7"]),
        8: ([1, 4, 6, 7, 11, 12], params["coverage_req_8"]),
        9: ([1, 3, 5, 6, 7, 12], params["coverage_req_9"]),
        10: ([1, 7, 8, 9, 10, 13], params["coverage_req_10"]),
        11: ([1, 5, 7, 10, 13, 14], params["coverage_req_11"]),
        12: ([1, 2, 8, 10, 12, 13, 14], params["coverage_req_12"]),
        13: ([4, 5, 6, 7, 8, 11], params["coverage_req_13"]),
        14: ([1, 3, 6, 7, 10], params["coverage_req_14"]),
        15: ([3, 4, 9, 12, 13, 14], params["coverage_req_15"]),
        16: ([1, 2, 3, 8, 10, 11], params["coverage_req_16"]),
        17: ([1, 2, 3, 4, 13], params["coverage_req_17"]),
        18: ([1, 2, 3, 7, 12, 14], params["coverage_req_18"]),
        19: ([1, 2, 3, 5, 7, 9, 12], params["coverage_req_19"]),
    }

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.Set(initialize=teams)
    model.COVERAGE = pyo.Set(initialize=sorted(coverage_sets.keys()))

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(team_cost[t] * m.x[t] for t in m.TEAMS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def coverage_rule(m, c):
        subset, req = coverage_sets[c]
        return sum(m.x[t] for t in subset) >= req

    model.coverage_con = pyo.Constraint(model.COVERAGE, rule=coverage_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}