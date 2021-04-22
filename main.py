rep_reduction = {
    1: 1.00,
    2: 0.97,
    3: 0.94,
    4: 0.92, 
    5: 0.89,
    6: 0.86,
    7: 0.83,
    8: 0.81,
    9: 0.78,
    10: 0.75,
    11: 0.73,
    12: 0.71,
    13: 0.70,
    14: 0.68,
    15: 0.67,
    16: 0.65,
    17: 0.64,
    18: 0.63,
    19: 0.61,
    20: 0.60,
    21: 0.59,
    22: 0.58,
    23: 0.57,
    24: 0.56,
    25: 0.55,
    26: 0.54,
    27: 0.53,
    28: 0.52,
    29: 0.51,
    30: 0.50
}

one_rm = int(input("What is your current 1RM?: "))
wod_reps = int(input("How many reps is your workout?: "))

# Move reps to within bounds
if wod_reps > 30:
    wod_reps = 30

rep_reduction_factor = rep_reduction[wod_reps]

wod_weight = one_rm * rep_reduction_factor

wod_weight_round = int(wod_weight - wod_weight % 5)

print(f"For a 1RM of {one_rm}#, the recommended weight is no more than {wod_weight_round}# for {wod_reps} reps.")