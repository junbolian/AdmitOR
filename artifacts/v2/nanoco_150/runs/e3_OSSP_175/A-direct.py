import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    pt = params["processing_times"]
    # Structural sizes: 3 jobs, 3 machines
    J = list(range(3))
    M = list(range(3))

    # Big-M per (job, machine) pair
    def bigM(j, i):
        s = sum(pt[r][i] for r in J) + sum(pt[j][r] for r in M)
        return float(s)

    model = pyo.ConcreteModel()

    # Decision variables
    # x[j,i,k] = 1 if job j is the k-th operation on machine i
    # Actually index formulation: y[j,i] position handled via ordering binaries.
    # Use classic disjunctive modeling: s[j,i] start times, z[j,i,k] machine sequencing.
    model.s = pyo.Var(J, M, within=pyo.NonNegativeReals, bounds=(0, None))
    model.C = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, None))
    # Job sequencing binaries: a[j,i,p,q] = 1 if op (j,p) precedes op (j,q) for same job j
    # Machine sequencing binaries: b[i,j,k] = 1 if job j precedes job k on machine i
    model.a = pyo.Var(J, M, M, within=pyo.Binary)
    model.b = pyo.Var(M, J, J, within=pyo.Binary)

    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    model.cons = pyo.ConstraintList()

    # Each job's operations are totally ordered (disjunctive) on its two machines:
    # for each job and each unordered pair of machines p<q:
    #   either s[j,p] + pt[j,p] <= s[j,q]  or  s[j,q] + pt[j,q] <= s[j,p]
    for j in J:
        for p in M:
            for q in M:
                if p < q:
                    M_pq = bigM(j, p)
                    model.cons.add(
                        model.s[j, p] + float(pt[j][p]) <= model.s[j, q] + M_pq * (1 - model.a[j, p, q])
                    )
                    model.cons.add(
                        model.s[j, q] + float(pt[j][q]) <= model.s[j, p] + M_pq * model.a[j, p, q]
                    )

    # Machine capacity: for each machine i, each pair of jobs j<k:
    #   either s[j,i] + pt[j,i] <= s[k,i]  or  s[k,i] + pt[k,i] <= s[j,i]
    for i in M:
        for j in J:
            for k in J:
                if j < k:
                    M_jk = bigM(j, i) + bigM(k, i)
                    model.cons.add(
                        model.s[j, i] + float(pt[j][i]) <= model.s[k, i] + M_jk * (1 - model.b[i, j, k])
                    )
                    model.cons.add(
                        model.s[k, i] + float(pt[k][i]) <= model.s[j, i] + M_jk * model.b[i, j, k]
                    )

    # Makespan: C >= s[j,i] + pt[j,i] for all j,i
    for j in J:
        for i in M:
            model.cons.add(model.C >= model.s[j, i] + float(pt[j][i]))

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}