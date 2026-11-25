import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["package_weights"]
    capacity = params["truck_capacity"]
    n_trucks = int(params["max_trucks"])
    n_packages = len(weights)

    packages = list(range(n_packages))
    trucks = list(range(n_trucks))

    model = pyo.ConcreteModel()

    # Decision variables
    model.x = pyo.Var(packages, trucks, domain=pyo.Binary)  # assign package to truck
    model.y = pyo.Var(trucks, domain=pyo.Binary)            # truck used

    # Objective: minimize number of trucks used (weighted slightly by index to break symmetry)
    def obj_rule(m):
        return sum(m.y[t] for t in trucks)
    model.total_trucks = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each package assigned to exactly one truck
    def assign_rule(m, p):
        return sum(m.x[p, t] for t in trucks) == 1
    model.assign = pyo.Constraint(packages, rule=assign_rule)

    # Capacity constraint per truck
    def cap_rule(m, t):
        return sum(weights[p] * m.x[p, t] for p in packages) <= capacity * m.y[t]
    model.capacity = pyo.Constraint(trucks, rule=cap_rule)

    # Symmetry breaking: truck t can only be used if truck t-1 is used
    def sym_rule(m, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.y[t] <= m.y[t - 1]
    model.symmetry = pyo.Constraint(trucks, rule=sym_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_trucks))
    return {"objective": obj_val, "status": "optimal"}