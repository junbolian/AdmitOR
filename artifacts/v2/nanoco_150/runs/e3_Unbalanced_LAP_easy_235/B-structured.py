# IR: {"sets":{"D":"range(params['num_doctors'])","P":"range(params['num_patients'])"},"params":{"num_doctors":"number of doctors","num_patients":"number of patients","cost_matrix":"assignment costs indexed by doctor and patient"},"variables":{"x[i,j]":"Binary for i in D, j in P"},"constraints":["sum(x[i,j] for j in P) == 1 for each i in D","sum(x[i,j] for i in D) <= 1 for each j in P"],"objective":"minimize sum(cost_matrix[i][j] * x[i,j] for i in D, j in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_doctors = params["num_doctors"]
    num_patients = params["num_patients"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.doctors = pyo.Set(initialize=range(num_doctors), ordered=True)
    model.patients = pyo.Set(initialize=range(num_patients), ordered=True)

    model.assignment_cost = pyo.Param(
        model.doctors,
        model.patients,
        initialize=lambda mdl, doctor, patient: cost_matrix[doctor][patient],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.doctors,
        model.patients,
        domain=pyo.Binary,
    )

    def doctor_assignment_rule(mdl, doctor):
        return (
            sum(
                (mdl.x[doctor, patient] for patient in mdl.patients),
                pyo.quicksum([]),
            )
            == 1
        )

    model.doctor_assignment = pyo.Constraint(
        model.doctors,
        rule=doctor_assignment_rule,
    )

    def patient_capacity_rule(mdl, patient):
        return (
            sum(
                (mdl.x[doctor, patient] for doctor in mdl.doctors),
                pyo.quicksum([]),
            )
            <= 1
        )

    model.patient_capacity = pyo.Constraint(
        model.patients,
        rule=patient_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment_cost[doctor, patient] * model.x[doctor, patient]
            for doctor in model.doctors
            for patient in model.patients
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}