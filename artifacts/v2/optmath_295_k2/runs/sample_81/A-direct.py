import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]

    n_crates = 10
    n_trucks = 10

    crates = list(range(n_crates))
    trucks = list(range(n_trucks))

    model = pyo.ConcreteModel()

    # x[c, t] = 1 if crate c is assigned to truck t
    model.x = pyo.Var(crates, trucks, domain=pyo.Binary)
    # y[t] = 1 if truck t is used
    model.y = pyo.Var(trucks, domain=pyo.Binary)

    # Each crate assigned to exactly one truck
    model.assign = pyo.Constraint(
        crates,
        rule=lambda m, c: sum(m.x[c, t] for t in trucks) == 1,
    )

    # Capacity constraint per truck
    model.capacity = pyo.Constraint(
        trucks,
        rule=lambda m, t: sum(crate_weight * m.x[c, t] for c in crates)
        <= truck_capacity * m.y[t],
    )

    # Linking: if a truck carries anything it must be marked used
    model.link = pyo.Constraint(
        crates,
        trucks,
        rule=lambda m, c, t: m.x[c, t] <= m.y[t],
    )

    # Objective: minimize number of trucks used
    model.obj = pyo.Objective(
        expr=sum(model.y[t] for t in trucks),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}