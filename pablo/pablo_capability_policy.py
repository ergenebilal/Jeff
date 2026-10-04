"""Explicit Node admission. Existing names retain execution gates, never proof authority."""
LEGACY_ACTIONS=frozenset({
    'antigravity','run_antigravity','antigravity_task','antigravity_post','ping','shell',
    'read','read_file','file_read','read_file_content','file_list','list_files','list_dir','dir_list',
    'social_post','twitter_post','instagram_post','file_dialog_submit','upload_dialog',
    'window_list','window_focus','gui_click','gui_drag','gui_scroll','gui_coords','gui_type',
    'screenshot','vision_grounding','browser_open','browser_read','browser_act','browser_session',
    'pilot_run_session','pilot_status','youtube_play','whatsapp_send','whatsapp_draft',
    'marketing_list','marketing_send_approval','marketing_playbook',
})
ACCEPTED_CONTRACTS={
    'local_draft':{'approval_boundary':'private_local_draft_only','outcome_contract':'exact_input_bound_file_hash_and_size',
                   'recovery':'observe_without_replay','acceptance_tests':['test_local_draft_verification.py','test_work_tracking.py']},
    'local_draft_plan':{'approval_boundary':'private_local_draft_steps_and_owner_only_person_signal',
                        'outcome_contract':'every_child_independent_file_read','recovery':'no_replay_of_claimed_child',
                        'acceptance_tests':['test_work_plans.py','test_runtime_interruption.py']},
}


def admission(action):
    contract=ACCEPTED_CONTRACTS.get(action)
    if contract:
        required=('approval_boundary','outcome_contract','recovery','acceptance_tests')
        if not all(contract.get(k) for k in required):
            return {'admitted':False,'reason':'incomplete_contract','completion_authority':False}
        return {'admitted':True,'class':'accepted_contract','completion_authority':'independent_evidence_required',**contract}
    if action in LEGACY_ACTIONS:
        return {'admitted':True,'class':'legacy_execution_only','approval_boundary':'existing_owner_and_desktop_gates',
                'outcome_contract':None,'recovery':'inspect_without_replay','completion_authority':False}
    return {'admitted':False,'reason':'no_accepted_contract','completion_authority':False,
            'required':['approval_boundary','outcome_contract','recovery','acceptance_tests']}
