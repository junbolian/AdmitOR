import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cpu_capacity = params["cpu_capacity"]
    mem_capacity = params["mem_capacity"]
    cpu_demand = params["cpu_demand"]
    mem_demand = params["mem_demand"]

    n_vms = len(cpu_demand)
    n_servers = n_vms  # sufficient pool

    vms = range(n_vms)
    servers = range(n_servers)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(vms, servers, domain=pyo.Binary)
    model.y = pyo.Var(servers, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[j] for j in servers), sense=pyo.minimize)

    model.assign = pyo.Constraint(
        vms, rule=lambda mdl, i: sum(mdl.x[i, j] for j in servers) == 1
    )

    model.cpu = pyo.Constraint(
        servers,
        rule=lambda mdl, j: sum(cpu_demand[i] * mdl.x[i, j] for i in vms)
        <= cpu_capacity * mdl.y[j],
    )

    model.mem = pyo.Constraint(
        servers,
        rule=lambda mdl, j: sum(mem_demand[i] * mdl.x[i, j] for i in vms)
        <= mem_capacity * mdl.y[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}