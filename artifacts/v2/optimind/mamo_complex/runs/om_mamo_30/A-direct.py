import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(8))
    source = 0
    sink = 7

    cap_data = {
        (0,1): params["capacity_0_1"],
        (0,2): params["capacity_0_2"],
        (0,3): params["capacity_0_3"],
        (0,5): params["capacity_0_5"],
        (0,6): params["capacity_0_6"],
        (0,7): params["capacity_0_7"],
        (1,0): params["capacity_1_0"],
        (1,2): params["capacity_1_2"],
        (1,3): params["capacity_1_3"],
        (1,4): params["capacity_1_4"],
        (1,5): params["capacity_1_5"],
        (1,6): params["capacity_1_6"],
        (2,0): params["capacity_2_0"],
        (2,1): params["capacity_2_1"],
        (2,3): params["capacity_2_3"],
        (2,4): params["capacity_2_4"],
        (2,5): params["capacity_2_5"],
        (2,6): params["capacity_2_6"],
        (2,7): params["capacity_2_7"],
        (3,0): params["capacity_3_0"],
        (3,1): params["capacity_3_1"],
        (3,2): params["capacity_3_2"],
        (3,4): params["capacity_3_4"],
        (3,5): params["capacity_3_5"],
        (3,7): params["capacity_3_7"],
        (4,0): params["capacity_4_0"],
        (4,1): params["capacity_4_1"],
        (4,2): params["capacity_4_2"],
        (4,3): params["capacity_4_3"],
        (4,5): params["capacity_4_5"],
        (4,6): params["capacity_4_6"],
        (4,7): params["capacity_4_7"],
        (5,0): params["capacity_5_0"],
        (5,1): params["capacity_5_1"],
        (5,2): params["capacity_5_2"],
        (5,3): params["capacity_5_3"],
        (5,4): params["capacity_5_4"],
        (5,6): params["capacity_5_6"],
        (5,7): params["capacity_5_7"],
        (6,0): params["capacity_6_0"],
        (6,1): params["capacity_6_1"],
        (6,2): params["capacity_6_2"],
        (6,3): params["capacity_6_3"],
        (6,4): params["capacity_6_4"],
        (6,5): params["capacity_6_5"],
        (6,7): params["capacity_6_7"],
        (7,0): params["capacity_7_0"],
        (7,1): params["capacity_7_1"],
        (7,3): params["capacity_7_3"],
        (7,4): params["capacity_7_4"],
        (7,5): params["capacity_7_5"],
        (7,6): params["capacity_7_6"],
    }

    arcs = [a for a in cap_data if cap_data[a] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def flow_bounds(mdl, i, j):
        return (0, cap_data[(i, j)])
    model.flow = pyo.Var(model.arcs, bounds=flow_bounds)

    model.obj = pyo.Objective(expr=sum(model.flow[a] for a in arcs if a[0] == source and a[1] == sink), sense=pyo.maximize)

    def flow_balance(mdl, n):
        out_flow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        in_flow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        if n == source:
            return out_flow - in_flow >= 0
        elif n == sink:
            return in_flow - out_flow >= 0
        else:
            return out_flow - in_flow == 0
    model.balance = pyo.Constraint(nodes, rule=flow_balance)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}