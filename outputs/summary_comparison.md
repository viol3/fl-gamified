# Flower vs Unity Comparison

## Summary
- Flower summary: outputs/flower_comparison_summary.json
- Unity summary: outputs/unity_comparison_summary.json
- Final accuracy diff: 0.080869
- Flower selected total: 331
- Unity selected total: 327
- Flower total samples: 46239
- Unity total samples: 45524
- Flower config rounds: 100
- Unity config rounds: 100

## Biggest Round Gaps
- Round 1: flower selected=3, unity selected=7, flower samples=485, unity samples=984, flower acc=0.717061, unity acc=0.742865
- Round 2: flower selected=3, unity selected=1, flower samples=444, unity samples=90, flower acc=0.745375, unity acc=0.680093
- Round 3: flower selected=3, unity selected=2, flower samples=495, unity samples=225, flower acc=0.728211, unity acc=0.743422
- Round 4: flower selected=4, unity selected=2, flower samples=535, unity samples=381, flower acc=0.797310, unity acc=0.763038
- Round 5: flower selected=3, unity selected=5, flower samples=348, unity samples=652, flower acc=0.808649, unity acc=0.832512
- Round 6: flower selected=1, unity selected=5, flower samples=181, unity samples=869, flower acc=0.839065, unity acc=0.855236
- Round 7: flower selected=3, unity selected=3, flower samples=532, unity samples=396, flower acc=0.833250, unity acc=0.842418
- Round 8: flower selected=5, unity selected=0, flower samples=665, unity samples=0, flower acc=0.845747, unity acc=0.822418
- Round 9: flower selected=7, unity selected=3, flower samples=1023, unity samples=463, flower acc=0.865389, unity acc=0.827422
- Round 10: flower selected=1, unity selected=2, flower samples=90, unity samples=282, flower acc=0.786116, unity acc=0.806396

## Client Differences
- Client 1: different fields = battery_level, fatigue, local_model_accuracy, participation_streak, total_participations
- Client 2: different fields = battery_level, local_model_accuracy, total_participations
- Client 3: different fields = battery_level, local_model_accuracy, total_participations
- Client 4: different fields = battery_level, fatigue, local_model_accuracy, participation_streak
- Client 5: different fields = battery_level, local_model_accuracy, total_participations
- Client 6: different fields = battery_level, fatigue, local_model_accuracy, participation_streak, total_participations
- Client 7: different fields = battery_level, local_model_accuracy, total_participations
- Client 8: different fields = battery_level, local_model_accuracy, total_participations
- Client 9: different fields = battery_level, fatigue, local_model_accuracy, participation_streak, total_participations
- Client 10: different fields = battery_level, fatigue, local_model_accuracy, participation_streak
