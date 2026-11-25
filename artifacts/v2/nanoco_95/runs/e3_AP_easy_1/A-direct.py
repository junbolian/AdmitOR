import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_vms = len(cost_matrix)
    num_nodes = len(cost_matrix[0])

    model = pyo.ConcreteModel()
    model.VMS = pyo.RangeSet(0, num_vms - 1)
    model.NODES = pyo.RangeSet(0, num_nodes - 1)

    model.x = pyo.Var(model.VMS, model.NODES, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for i in m.VMS for j in m.NODES)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def vm_rule(m, i):
        return sum(m.x[i, j] for j in m.NODES) == 1

    model.vm_con = pyo.Constraint(model.VMS, rule=vm_rule)

    def node_rule(m, j):
        return sum(m.x[i, j] for i in m.VMS) == 1

    model.node_con = pyo.Constraint(model.NODES, rule=node_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}