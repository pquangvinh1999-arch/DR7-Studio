"""Motion acceptance gate, independent from texture/timing/hash correctness.

Visual anatomy cannot be proven by one connected-component scalar. A recorded
structural failure always blocks delivery, and reviews are bound to atlas bytes.
"""
REQUIRED_CHECKS={'body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds'}
ALLOWED_METHODS={'imagegen_complete_body_keyframes','image_to_video','existing_complete_source_frames'}

def assess_motion_quality(review, atlas_sha256, render_contract=None):
    errors=[]
    if not review:
        return {'ok_for_human_test':False,'release_approved':False,'status':'pending_visual_review','errors':['Motion review is missing.']}
    if review.get('status') in {'fail','failed','rejected'}:
        errors.append('Motion FAIL: structural/turning defect remains recorded.')
    if review.get('method') not in ALLOWED_METHODS:
        errors.append('Motion FAIL: method is missing or uses rejected cut-part/warp motion.')
    if review.get('atlas_sha256')!=atlas_sha256:
        errors.append('Motion review is stale: atlas SHA-256 changed.')
    checks=review.get('checks',{})
    if checks.get('character_identity') is False:
        errors.append('Character identity FAIL: clip does not match the canonical character master.')
    for name in sorted(REQUIRED_CHECKS):
        if name == 'perspective_turns' and render_contract:
            loc = render_contract.get('locomotion', {})
            facing = render_contract.get('facing', {})
            if (loc.get('kind') == 'stationary'
                    and loc.get('clip') == 'idle'
                    and loc.get('allow_turn_or_flip') is False
                    and render_contract.get('body_clips') == ['idle']
                    and facing.get('camera_view') == 'front_only'
                    and facing.get('directions') == ['front']
                    and facing.get('owner_instruction')
                    and review.get('not_applicable_checks', {}).get('perspective_turns')):
                continue
            turning = render_contract.get('turning', {})
            burrow = render_contract.get('chilopoda', {}).get('burrow_turn', {})
            if (turning.get('method') == 'burrow_reorient_while_hidden'
                    and turning.get('owner_instruction')
                    and burrow.get('relocate') is False
                    and burrow.get('hidden_start_tick', 0) < burrow.get('emerge_start_tick', 0)):
                if checks.get('burrow_turn_bidirectional') is not True:
                    errors.append('Motion review pending/FAIL: burrow_turn_bidirectional')
                continue
        if checks.get(name) is not True:errors.append('Motion review pending/FAIL: '+name)
    if review.get('unresolved_structural_failures'):
        errors.append('Motion FAIL: unresolved structural failures exist.')
    if review.get('status') not in {'reviewed_pending_owner','owner_approved'}:
        errors.append('Motion review has not reached reviewable status.')
    return {'ok_for_human_test':not errors,'release_approved':not errors and review.get('status')=='owner_approved',
            'status':review.get('status','pending_visual_review'),'errors':errors}
