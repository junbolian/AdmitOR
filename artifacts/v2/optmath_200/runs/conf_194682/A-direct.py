import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    package_weight = params["package_weight"]
    truck_capacity = params["truck_capacity"]

    num_packages = 10
    num_trucks = 10

    model = pyo.ConcreteModel()
    model.PACKAGES = pyo.Set(initialize=range(num_packages))
    model.TRUCKS = pyo.Set(initialize=range(num_trucks))

    model.assign = pyo.Var(model.PACKAGES, model.TRUCKS, domain=pyo.Binary)
    model.used = pyo.Var(model.TRUCKS, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.used[t] for t in model.TRUCKS), sense=pyo.minimize)

    model.package_constraint = pyo.Constraint(
        model.PACKAGES,
        rule=lambda m, p: sum(m.assign[p, t] for t in m.TRUCKS) == 1,
    )

    model.capacity_constraint = pyo.Constraint(
        model.TRUCKS,
        rule=lambda m, t: sum(package_weight * m.assign[p, t] for p in m.PACKAGES)
        <= truck_capacity * m.used[t],
    )

    model.link_constraint = pyo.Constraint(
        model.PACKAGES,
        model.TRUCKS,
        rule=lambda m, p, t: m.assign[p, t] <= m.used[t],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}