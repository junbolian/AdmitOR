import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_weights = params["supply_weights"]
    capacity = params["hospital_capacity"]

    num_supplies = len(supply_weights)
    num_hospitals = num_supplies  # upper bound on hospitals needed

    supplies = range(num_supplies)
    hospitals = range(num_hospitals)

    model = pyo.ConcreteModel()

    # x[i, j] = 1 if supply i is assigned to hospital j
    model.x = pyo.Var(supplies, hospitals, domain=pyo.Binary)

    # y[j] = 1 if hospital j is used
    model.y = pyo.Var(hospitals, domain=pyo.Binary)

    # Objective: minimize number of hospitals used
    model.total_hospitals = pyo.Objective(
        expr=sum(model.y[j] for j in hospitals),
        sense=pyo.minimize,
    )

    # Assignment constraint: each supply assigned to exactly one hospital
    def assignment_rule(m, i):
        return sum(m.x[i, j] for j in hospitals) == 1

    model.assignment = pyo.Constraint(supplies, rule=assignment_rule)

    # Capacity constraint: total weight in each hospital <= capacity
    def capacity_rule(m, j):
        return sum(supply_weights[i] * m.x[i, j] for i in supplies) <= capacity * m.y[j]

    model.capacity = pyo.Constraint(hospitals, rule=capacity_rule)

    # Linking constraint: if a supply is assigned to hospital j, y[j] must be 1
    def linking_rule(m, i, j):
        return m.x[i, j] <= m.y[j]

    model.linking = pyo.Constraint(supplies, hospitals, rule=linking_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_hospitals))
    return {"objective": obj_val, "status": "optimal"}