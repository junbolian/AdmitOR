import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ['S', '2', '3', '4', '5', '6', '7', 'T']
    edge_list = [
        ('S', '2'), ('S', '3'),
        ('2', 'S'), ('2', '4'), ('2', '3'),
        ('3', 'S'), ('3', '2'), ('3', '5'), ('3', '6'),
        ('4', '2'), ('4', '6'),
        ('5', '3'), ('5', 'T'),
        ('6', '3'), ('6', '4'), ('6', '7'),
        ('7', '6'), ('7', 'T'),
        ('T', '5'), ('T', '7'),
    ]
    weights = {}
    for edge in edge_list:
        key = "w_" + edge[0] + "_" + edge[1]
        weights[edge] = params[key]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edge_list, dimen=2)
    model.flow = pyo.Var(model.edges, bounds=(0, 1))

    def flow_balance_rule(mdl, node):
        out_flow = sum(mdl.flow[i, j] for (i, j) in edge_list if i == node)
        in_flow = sum(mdl.flow[i, j] for (i, j) in edge_list if j == node)
        if node == 'S':
            return out_flow - in_flow == 1
        elif node == 'T':
            return out_flow - in_flow == -1
        else:
            return out_flow - in_flow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def obj_rule(mdl):
        return sum(weights[edge] * mdl.flow[edge] for edge in edge_list)

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_distance))
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": round(obj_val), "status": "optimal"}