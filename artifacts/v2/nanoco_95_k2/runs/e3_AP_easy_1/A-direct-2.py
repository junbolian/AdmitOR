import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    n_vms = len(cost_matrix)
    n_nodes = len(cost_matrix[0])
    vms = range(n_vms)
    nodes = range(n_nodes)

    model = pyo.ConcreteModel()
    model.VMS = pyo.Set(initialize=list(vms))
    model.NODES = pyo.Set(initialize=list(nodes))

    model.x = pyo.Var(model.VMS, model.NODES, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for i in m.VMS for j in m.NODES)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def vm_rule(m, i):
        return sum(m.x[i, j] for j in m.NODES) == 1

    model.vm_constraint = pyo.Constraint(model.VMS, rule=vm_rule)

    def node_rule(m, j):
        return sum(m.x[i, j] for i in m.VMS) == 1

    model.node_constraint = pyo.Constraint(model.NODES, rule=node_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}