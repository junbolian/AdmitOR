import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_substances = int(params["num_substances"])
    edge_list = params["edge_list"]

    substances = list(range(num_substances))
    max_sections = num_substances

    model = pyo.ConcreteModel()

    model.SUBSTANCES = pyo.Set(initialize=substances)
    model.SECTIONS = pyo.Set(initialize=list(range(max_sections)))

    model.x = pyo.Var(model.SUBSTANCES, model.SECTIONS, domain=pyo.Binary)
    model.y = pyo.Var(model.SECTIONS, domain=pyo.Binary)

    # Each substance assigned to exactly one section
    model.assign = pyo.Constraint(
        model.SUBSTANCES,
        rule=lambda m, i: sum(m.x[i, s] for s in m.SECTIONS) == 1,
    )

    # Incompatibility constraints
    model.incompat = pyo.ConstraintList()
    for (i, j) in edge_list:
        for s in model.SECTIONS:
            model.incompat.add(model.x[i, s] + model.x[j, s] <= 1)

    # Linking: substance in section implies section used
    model.link = pyo.Constraint(
        model.SUBSTANCES,
        model.SECTIONS,
        rule=lambda m, i, s: m.x[i, s] <= m.y[s],
    )

    # Objective: minimize number of sections used
    model.obj = pyo.Objective(expr=sum(model.y[s] for s in model.SECTIONS), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}