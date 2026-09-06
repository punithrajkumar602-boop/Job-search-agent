"""
The human-in-the-loop checkpoint. Every tailored application must pass
through here before its status can become "approved". This module
intentionally has no "auto-approve everything" mode -- that defeats the
entire point of the gate. If you want faster review, make the CLI output
terser, not the gate optional.
"""


def review(tailored_app, non_interactive_decisions: dict = None) -> str:
    """
    Shows one tailored application and asks for a decision.
    non_interactive_decisions: optional {job_id: "approve"/"reject"} map,
    used only for scripted demos/tests -- normal runs should omit this
    and go through the real input() prompt below.
    """
    job = tailored_app.job

    if non_interactive_decisions is not None:
        decision = non_interactive_decisions.get(job.job_id, "reject")
        tailored_app.status = "approved" if decision == "approve" else "rejected"
        return tailored_app.status

    print("\n" + "=" * 70)
    print(f"{job.title} — {job.company}  (fit score: {tailored_app.fit_score:.2f})")
    print("-" * 70)
    print(f"Summary: {tailored_app.resume_summary}\n")
    print(f"Subject: {tailored_app.email_subject}")
    print(f"Body:\n{tailored_app.email_body}")
    print("=" * 70)

    choice = input("Approve this application? [y/n/skip]: ").strip().lower()
    if choice == "y":
        tailored_app.status = "approved"
    elif choice == "skip":
        tailored_app.status = "skipped"
    else:
        tailored_app.status = "rejected"
    return tailored_app.status
