import clearance_math
import datetime
import numpy

#Test case 1
#Case 1 sample
print("Test one sample adult")
age = 16 #years
height = 166 #cm
weight = 48 # kg

vial_weight_before = 4.0540 #g
vial_weight_after  = 3.1060 #g

thinning_factor = 980 
std_cnt = 8071 #cpm

dosis = 7498281 #Cpm
dosis_Calc = clearance_math.dosis(vial_weight_before - vial_weight_after, thinning_factor, std_cnt)

BSA = 1.52
BSA_calc = clearance_math.surface_area(height,weight)

print("Body surface area calc:", BSA_calc, "difference: ", BSA_calc - BSA)
print("Dosis Calcution:",  dosis == dosis_Calc)

inj_time      = datetime.datetime(2019,1,21,9,14)
sample_1_time = datetime.datetime(2019,1,21,12,35) 

sample_1_CPM = 51 #cpm

GFR = 134
GFR_N = 152

Calc_GFR, Calc_GFR_N = clearance_math.calc_clearance(inj_time,[sample_1_time],[sample_1_CPM], BSA_calc, dosis_Calc)

print("Calculated GFR ",Calc_GFR,"True GFR:",GFR, "\nCalculated GFR Normalized:", Calc_GFR_N, "True GFR Normalized:", GFR_N, "\n\n")

clearance_math.generate_plot(
    numpy.array([[],[]]),
    numpy.array([[age],[Calc_GFR_N]]),
    "Test_case_1",
    show_fig=True,
    save_fig=False
)

#Test case 2
print("Test one sample child")
age = 4 
height = 94
weight = 14

vial_weight_before = 3.9830
vial_weight_after = 3.0160

thinning_factor = 840
std_cnt = 2898

dosis = 2353987
dosis_Calc = clearance_math.dosis(
    vial_weight_before - vial_weight_after,
    thinning_factor,
    std_cnt
)

BSA = 0.59
BSA_calc = clearance_math.surface_area(height, weight)

print("Body surface area calc:", BSA_calc, "difference: ", BSA_calc - BSA)
print("Dosis Calcution:",  dosis == dosis_Calc)

inj_time = datetime.datetime(2019,1,21,10,45)
sample_1_time = datetime.datetime(2019,1,21,12,48)

sample_1_CPM = 225 #Cpm

GFR = 29
GFR_N = 85

Calc_GFR, Calc_GFR_N = clearance_math.calc_clearance(
    inj_time,
    [sample_1_time],
    [sample_1_CPM],
    BSA_calc,
    dosis_Calc,
    method="EPB"
)

print("Calculated GFR ",Calc_GFR,"True GFR:",GFR, "\nCalculated GFR Normalized:", Calc_GFR_N, "True GFR Normalized:", GFR_N , "\n\n")
clearance_math.generate_plot(
    numpy.array([[],[]]),
    numpy.array([[age],[Calc_GFR_N]]),
    "Test_case_2",
    save_fig=False,
    show_fig=True    
)

#Test case 3
print("Test Multiple sample")

age = 22 #years
height = 184 #cm
weight = 76 #KG

vial_weight_before = 4.3280 #g
vial_weight_after  = 3.1230 #g

thinning_factor = 917
std_cnt = 6246

dosis = 6901736
dosis_Calc = clearance_math.dosis(
    vial_weight_before - vial_weight_after,
    thinning_factor,
    std_cnt
)

BSA = 1.98
BSA_calc = clearance_math.surface_area(height, weight)

print("Body surface area calc:", BSA_calc, "difference: ", BSA_calc - BSA)
print("Dosis Calcution:",  dosis == dosis_Calc)

inj_time = datetime.datetime(2019,1,4,8,56)
sample_1_time = datetime.datetime(2019,1,4,12,56)
sample_2_time = datetime.datetime(2019,1,4,13,16)
sample_3_time = datetime.datetime(2019,1,4,13,37)
sample_4_time = datetime.datetime(2019,1,4,13,57)

sample_1_CPM = 49
sample_2_CPM = 42
sample_3_CPM = 37
sample_4_CPM = 32

times = numpy.array([sample_1_time, sample_2_time, sample_3_time, sample_4_time])
cpms  = numpy.array([sample_1_CPM, sample_2_CPM, sample_3_CPM, sample_4_CPM])

GFR    = 143
GFR_N  = 129

Calc_GFR , Calc_GFR_N = clearance_math.calc_clearance(
    inj_time,
    times,
    cpms,
    BSA_calc,
    dosis_Calc,
    method = "Multi-4"
)

print("Calculated GFR ",Calc_GFR,"True GFR:",GFR, "\nCalculated GFR Normalized:", Calc_GFR_N, "True GFR Normalized:", GFR_N , "\n\n")
clearance_math.generate_plot(
    numpy.array([clearance_math.compute_times(inj_time, times),cpms]),
    numpy.array([[age],[Calc_GFR_N]]),
    "Test_case_3",
    show_fig=True,
    save_fig=False
)

clearance_math.generate_plot_text(
    weight,
    height,
    BSA,
    Calc_GFR,
    Calc_GFR_N,
    "TODO",
    age,
    "Test_case_3_text",
    show_fig=True,
    save_fig=False
)