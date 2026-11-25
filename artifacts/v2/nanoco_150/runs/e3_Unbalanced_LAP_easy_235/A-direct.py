import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_doctors = params["num_doctors"]
    num_patients = params["num_patients"]

    model = pyo.ConcreteModel()

    model.DOCTORS = pyo.RangeSet(0, num_doctors - 1)
    model.PATIENTS = pyo.RangeSet(0, num_patients - 1)

    model.assign = pyo.Var(model.DOCTORS, model.PATIENTS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            cost_matrix[i][j] * m.assign[i, j]
            for i in m.DOCTORS
            for j in m.PATIENTS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def doctor_rule(m, i):
        return sum(m.assign[i, j] for j in m.PATIENTS) == 1

    model.doctor_constraint = pyo.Constraint(model.DOCTORS, rule=doctor_rule)

    def patient_rule(m, j):
        return sum(m.assign[i, j] for i in m.DOCTORS) <= 1

    model.patient_constraint = pyo.Constraint(model.PATIENTS, rule=patient_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}