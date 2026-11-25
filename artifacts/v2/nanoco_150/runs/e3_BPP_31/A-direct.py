import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["vm_demands"]
    capacity = params["server_capacity"]

    n_vms = len(demands)
    n_servers = n_vms  # an upper bound on the number of servers needed

    model = pyo.ConcreteModel()

    model.VMS = pyo.RangeSet(0, n_vms - 1)
    model.SERVERS = pyo.RangeSet(0, n_servers - 1)

    # x[i, j] = 1 if VM i is assigned to server j
    model.x = pyo.Var(model.VMS, model.SERVERS, domain=pyo.Binary)

    # y[j] = 1 if server j is powered on
    model.y = pyo.Var(model.SERVERS, domain=pyo.Binary)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.SERVERS) == 1

    model.assign_con = pyo.Constraint(model.VMS, rule=assign_rule)

    def cap_rule(m, j):
        return sum(demands[i] * m.x[i, j] for i in m.VMS) <= capacity * m.y[j]

    model.cap_con = pyo.Constraint(model.SERVERS, rule=cap_rule)

    # symmetry breaking: server j can only be used if server j-1 is used
    def sym_rule(m, j):
        if j == 0:
            return pyo.Constraint.Skip
        return m.y[j] <= m.y[j - 1]

    model.sym_con = pyo.Constraint(model.SERVERS, rule=sym_rule)

    model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.SERVERS), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}