import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        ("S", "2", "w_S_2"),
        ("S", "3", "w_S_3"),
        ("2", "S", "w_2_S"),
        ("2", "4", "w_2_4"),
        ("2", "3", "w_2_3"),
        ("3", "S", "w_3_S"),
        ("3", "2", "w_3_2"),
        ("3", "5", "w_3_5"),
        ("3", "6", "w_3_6"),
        ("4", "2", "w_4_2"),
        ("4", "6", "w_4_6"),
        ("5", "3", "w_5_3"),
        ("5", "T", "w_5_T"),
        ("6", "3", "w_6_3"),
        ("6", "4", "w_6_4"),
        ("6", "7", "w_6_7"),
        ("7", "6", "w_7_6"),
        ("7", "T", "w_7_T"),
        ("T", "5", "w_T_5"),
        ("T", "7", "w_T_7"),
    ]
    nodes = ["S", "2", "3", "4", "5", "6", "7", "T"]

    model = pyo.ConcreteModel()
    model.edge_idx = pyo.RangeSet(0, len(edges) - 1)

    model.x = pyo.Var(model.edge_idx, domain=pyo.Binary)

    def obj_rule(m):
        return sum(params[edges[k][2]] * m.x[k] for k in m.edge_idx)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow balance: source sends 1, sink receives 1, others balanced
    def balance_rule(m, n):
        out_flow = sum(m.x[k] for k in m.edge_idx if edges[k][0] == n)
        in_flow = sum(m.x[k] for k in m.edge_idx if edges[k][1] == n)
        if n == "S":
            return out_flow - in_flow == 1
        elif n == "T":
            return out_flow - in_flow == -1
        else:
            return out_flow - in_flow == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}