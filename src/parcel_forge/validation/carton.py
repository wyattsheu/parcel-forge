"""Scenario-scoped carton acceptance.

Two repairs authorised by the user on 2026-09-17 (D060):
1. Settledness is measured from the trailing angle span. The articulation DOF
   velocity readback freezes at a stale nonzero value while a flap rests against a
   sustained contact, so it cannot decide whether a flap is still moving.
2. The legacy mixed-load gate is retired as a specification error, not relaxed.
   Its failing evidence stays on disk and the scenario stays runnable.
"""
import math

LEGACY_MIXED_SUPERSEDED={
 'status':'superseded_by_spec_error',
 'reason':'legacy-mixed requires the two minor flaps to open plastically while one major flap is held closed on top of them. On an RSC the minors fold under the majors, so the requirement is unreachable at any torque, not a defect of the asset.',
 'measured':'0.08 N.m moved the minors 0.57 deg in runs/20260917T105836Z_ext1_carton and 100 deg in runs/20260917T114330Z_ext1_carton once the majors had opened first.',
 'evidence_retained':['runs/20260917T105836Z_ext1_carton','runs/20260917T114330Z_ext1_carton'],
 'replaced_by':['opening-order','crease-coupon'],
 'note':'no threshold was lowered, no collision disabled; the scenario is retired and its old result files are unchanged'}


def trailing_angle_spans(rows,names,window_s):
    """Peak-to-peak joint angle over the last window_s of the run, per joint."""
    if window_s<=0 or not math.isfinite(window_s):raise ValueError('window_s must be positive and finite')
    if not rows:return [float('inf')]*len(names)
    end=max(row[1] for row in rows);spans=[]
    for name in names:
        angles=[float(row[3]) for row in rows if row[2]==name and row[1]>end-window_s]
        spans.append(max(angles)-min(angles) if angles else float('inf'))
    return spans


def evaluate_carton(config,names,rows,peak,maxplastic,states,final,vel,settle_window_s=1.0):
    scenario=config.get('scenario','legacy-mixed');result={};dt=config['dt_s']
    tolerance=config.get('opening_profile',{}).get('settled_max_rad_s',.02)
    spans=trailing_angle_spans(rows,names,settle_window_s);rates=[span/settle_window_s for span in spans]
    velocity_readback=[float(x) for x in vel]
    settled=all(rate<tolerance for rate in rates)
    result['settle_metrics']={'window_s':settle_window_s,'tolerance_rad_s':tolerance,'trailing_span_rad':spans,'trailing_rate_rad_s':rates,
     'velocity_readback_rad_s':velocity_readback,'velocity_readback_settled':max(abs(v) for v in velocity_readback)<tolerance if velocity_readback else False,
     'method':'gated on the trailing angle span; the DOF velocity readback is recorded but not gated because it holds a stale nonzero value under sustained contact'}
    finite=all(math.isfinite(float(v)) for row in rows for v in row if not isinstance(v,str))
    checks={'finite':finite,'four_flaps':len(names)==4,'settled':settled}
    if scenario=='legacy-mixed':
        low_index=names.index('HingeMajorYN')
        checks.update({'low_no_plastic':maxplastic[low_index]<1e-6,'high_plastic':all(maxplastic[i]>.01 for i in range(4) if i!=low_index),
         'low_returns_near_closed':abs(float(final[low_index]))<math.radians(6),'high_retains_open_angle':all(float(final[i])>math.radians(10) for i in range(4) if i!=low_index)})
        result['legacy_mixed']=dict(LEGACY_MIXED_SUPERSEDED,checks_recomputed=dict(checks))
        result['checks']=checks;result['status']='superseded'
        return result
    result['checks']=checks
    if scenario=='opening-order':
        profile=config['opening_profile']
        opening_checks={'finite':finite,'four_flaps':checks['four_flaps'],'all_opened':all(math.degrees(x)>profile['peak_min_deg'] for x in peak),'all_plastic':all(math.degrees(abs(s.target))>profile['plastic_min_deg'] for s in states),'all_retained_open':all(math.degrees(float(x))>profile['residual_min_deg'] for x in final),'settled':settled}
        result['opening_checks']=opening_checks;result['opening_diagnostic_status']='pass' if all(opening_checks.values()) else 'fail'
        result['legacy_gate_applicability']='legacy mixed-load gate retired as a spec error; this scenario intentionally has no low-load control'
        result['status']=result['opening_diagnostic_status']
        return result
    if scenario in ['crease-coupon','crease-cyclic']:
        low=names.index('HingeMinorXP');high=names.index('HingeMinorXN')
        coupon_settled=all(rates[i]<tolerance for i in [low,high])
        coupon_checks={'finite':finite,'low_no_plastic':maxplastic[low]<1e-6,'low_returns_near_closed':abs(float(final[low]))<math.radians(6),'high_plastic':maxplastic[high]>.01,'high_retains_open_angle':float(final[high])>math.radians(10),'settled':coupon_settled}
        result['coupon_checks']=coupon_checks;result['coupon_diagnostic_status']='pass' if all(coupon_checks.values()) else 'fail'
        result['coupon_scope']='major flaps held open by force drives; minor XP low load, minor XN high load, minor actuators released at6s; collision retained; not free release of all four flaps'
        result['status']=result['coupon_diagnostic_status']
    if scenario=='crease-cyclic':
        result['coupon_scope']='major flaps held open; minors loaded over four cycles; high-load minor actively closed three times; minor drives released at24s; not all-flap free release'
        high_rows=[row for row in rows if row[2]=='HingeMinorXN'];profile=config['cycle_profile']
        yield_ends=[min(high_rows,key=lambda row:abs(row[1]-(end-dt)))[7] for start,end in profile['opening_intervals_s']]
        closing_min=[min(row[3] for row in high_rows if start<=row[1]<end) for start,end in profile['closing_intervals_s']]
        cyclic_checks={'softening_observed':yield_ends[-1]<yield_ends[0],'yield_floor_respected':min(row[7] for row in high_rows)>=profile['yield_floor_nm'],'closing_reversals':all(angle<0 for angle in closing_min)}
        result['cyclic_checks']=cyclic_checks;result['cycle_end_yield_nm']=yield_ends;result['cyclic_diagnostic_status']='pass' if all(cyclic_checks.values()) else 'fail'
        result['status']='pass' if result['coupon_diagnostic_status']=='pass' and result['cyclic_diagnostic_status']=='pass' else 'fail'
    return result
