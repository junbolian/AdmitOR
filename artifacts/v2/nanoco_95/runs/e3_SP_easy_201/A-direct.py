import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (0, 7), (1, 2), (1, 7), (2, 3), (2, 6), (3, 4), (3, 5),
        (3, 8), (3, 9), (4, 5), (4, 8), (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]

    cost = {
        (0, 1): params["arc_cost_0_1"],
        (0, 7): params["arc_cost_0_7"],
        (1, 2): params["arc_cost_1_2"],
        (1, 7): params["arc_cost_1_7"],
        (2, 3): params["arc_cost_2_3"],
        (2, 6): params["arc_cost_2_6"],
        (3, 4): params["arc_cost_3_4"],
        (3, 5): params["arc_cost_3_5"],
        (3, 8): params["arc_cost_3_8"],
        (3, 9): params["arc_cost_3_9"],
        (4, 5): params["arc_cost_4_5"],
        (4, 8): params["arc_cost_4_8"],
        (5, 6): params["arc_cost_5_6"],
        (6, 7): params["arc_cost_6_7"],
        (7, 8): params["arc_cost_7_8"],
        (7, 9): params["arc_cost_7_9"],
        (8, 9): params["arc_cost_8_9"],
    }

    nodes = list(range(10))
    supply = {0: params["supply_source"]}
    supply[9] = -params["demand_sink"]
    for intermediate_node in range(1, 9):
        supply[intermediate_node] = params["intermediate_supply"]

    model = pyo.ConcreteModel()
    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals, bounds=(0, 1))

    def obj_rule(mdl):
        return sum(cost[arc] * mdl.x[arc] for arc in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.flow_con = pyo.ConstraintList()
    for node in nodes:
        outflow = sum(model.x[arc] for arc in arcs if arc[0] == node)
        inflow = sum(model.x[arc] for arc in arcs if arc[1] == node)
        model.flow_con.add(outflow - inflow == supply[node])

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}